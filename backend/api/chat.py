"""
对话API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response
from starlette.types import Receive, Scope, Send
from typing import List
import json
import asyncio

from database import get_db
from schemas import (
    SessionCreate, SessionResponse, MessageCreate, 
    MessageResponse, ConversationResponse
)
from services.auth_service import AuthService
from services.session_service import SessionService
from services.message_service import MessageService
from services.ai.workflow import ai_workflow
from services.attachment_service import AttachmentService
from services.smart_questions_service import smart_questions_service

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()
session_service = SessionService()
message_service = MessageService()
attachment_service = AttachmentService()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    """获取当前用户ID"""
    try:
        user = await auth_service.get_current_user(db, credentials.credentials)
        return user.id
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/session", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建新会话"""
    session = await session_service.create_session(db, user_id, session_data)
    return session


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的所有会话"""
    sessions = await session_service.list_user_sessions(db, user_id, limit, offset)
    return sessions


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取会话详情"""
    session = await session_service.get_session(db, session_id, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    return session


@router.get("/session/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    limit: int = 100,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取会话的所有消息"""
    # 验证会话所有权
    session = await session_service.get_session(db, session_id, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    messages = await message_service.get_session_messages(db, session_id, limit)
    return messages


@router.post("/message", response_model=ConversationResponse)
async def send_message(
    message_data: MessageCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """发送消息并获取AI回复"""
    # 验证会话所有权
    session = await session_service.get_session(db, message_data.session_id, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    # 保存用户消息
    user_message = await message_service.save_message(
        db,
        session_id=message_data.session_id,
        role="user",
        content=message_data.message
    )

    if session.message_count == 0:
        title = None
        if message_data.message.strip():
            title = session_service.generate_session_title(message_data.message)
        elif message_data.attachments:
            first_attachment = message_data.attachments[0]
            file_name = None
            if isinstance(first_attachment, dict):
                file_name = first_attachment.get("file_name") or first_attachment.get("file_id")
            elif isinstance(first_attachment, str):
                file_name = first_attachment
            else:
                file_name = getattr(first_attachment, "file_name", None) or getattr(first_attachment, "file_id", None)
            if file_name:
                base_name = file_name.rsplit(".", 1)[0]
                title = session_service.generate_session_title(base_name)
        if title:
            await session_service.update_session_title(db, message_data.session_id, title)

    # 保存附件
    saved_attachments = []
    if message_data.attachments:
        saved_attachments = await attachment_service.save_attachments(
            db,
            message_id=user_message.id,
            attachments=message_data.attachments
        )

    # 构建附件信息（包含 file_path）
    attachment_info = [
        {
            "file_id": att.id,
            "file_name": att.file_name,
            "file_type": att.file_type,
            "file_size": att.file_size,
            "file_path": att.file_path
        }
        for att in saved_attachments
    ]

    # 处理消息
    result = await ai_workflow.process_message(
        user_id=user_id,
        session_id=message_data.session_id,
        message=message_data.message,
        attachments=attachment_info
    )

    # 保存AI回复
    ai_message = await message_service.save_message(
        db,
        session_id=message_data.session_id,
        role="assistant",
        content=result["response"],
        metadata={
            "intent": result.get("intent"),
            "sources": result.get("sources"),
            "ticket_id": result.get("ticket_id")
        }
    )

    # 更新会话活动时间
    await session_service.update_session_activity(db, message_data.session_id)

    return ConversationResponse(
        message_id=ai_message.id,
        content=result["response"],
        sources=result.get("sources"),
        intent=result.get("intent"),
        ticket_id=result.get("ticket_id"),
        processing_time=result.get("processing_time"),
        quick_actions=result.get("quick_actions"),  # 新增
        recommended_products=result.get("recommended_products")  # 新增
    )


class SSEResponse(Response):
    """手动控制 ASGI send 的 SSE 响应，确保每个事件立即 flush"""

    def __init__(self, handler, status_code=200):
        self.handler = handler
        self.status_code = status_code
        self.background = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": [
                [b"content-type", b"text/event-stream; charset=utf-8"],
                [b"cache-control", b"no-cache, no-store"],
                [b"connection", b"keep-alive"],
                [b"x-accel-buffering", b"no"],
            ],
        })

        async def send_event(data: dict):
            payload = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            await send({
                "type": "http.response.body",
                "body": payload.encode("utf-8"),
                "more_body": True,
            })

        await self.handler(send_event)

        await send({"type": "http.response.body", "body": b"", "more_body": False})


@router.post("/stream")
async def stream_message(
    message_data: MessageCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """流式发送消息（Server-Sent Events）- 实时生成"""
    # 验证会话所有权
    session = await session_service.get_session(db, message_data.session_id, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    async def handle_stream(send_event):
        # 保存用户消息
        await message_service.save_message(
            db,
            session_id=message_data.session_id,
            role="user",
            content=message_data.message
        )

        if session.message_count == 0:
            title = None
            if message_data.message.strip():
                title = session_service.generate_session_title(message_data.message)
            elif message_data.attachments:
                first_attachment = message_data.attachments[0]
                file_name = None
                if isinstance(first_attachment, dict):
                    file_name = first_attachment.get("file_name") or first_attachment.get("file_id")
                elif isinstance(first_attachment, str):
                    file_name = first_attachment
                else:
                    file_name = getattr(first_attachment, "file_name", None) or getattr(first_attachment, "file_id", None)
                if file_name:
                    base_name = file_name.rsplit(".", 1)[0]
                    title = session_service.generate_session_title(base_name)
            if title:
                await session_service.update_session_title(db, message_data.session_id, title)

        # 发送开始事件
        await send_event({"type": "start"})

        # 构建附件信息
        attachment_info = []
        if message_data.attachments:
            for att in message_data.attachments:
                if isinstance(att, dict):
                    file_id = att.get("file_id")
                    file_name = att.get("file_name")
                    file_type = att.get("file_type")
                    file_size = att.get("file_size")
                    file_path = att.get("file_path")
                else:
                    file_id = getattr(att, "file_id", None)
                    file_name = getattr(att, "file_name", None)
                    file_type = getattr(att, "file_type", None)
                    file_size = getattr(att, "file_size", None)
                    file_path = getattr(att, "file_path", None)
                attachment_info.append({
                    "file_id": file_id,
                    "file_name": file_name,
                    "file_type": file_type,
                    "file_size": file_size,
                    "file_path": file_path
                })

        # 阶段1: 意图识别
        state = await ai_workflow.prepare_intent(
            user_id=user_id,
            session_id=message_data.session_id,
            message=message_data.message,
            attachments=attachment_info
        )
        intent = state.get("intent", "问答")
        await send_event({"type": "intent", "intent": intent})

        # 阶段2: 流式生成回答，逐 token 发送
        full_response = ""
        async for event in ai_workflow.generate_response_stream(state):
            if event["type"] == "content":
                full_response += event["delta"]
                await send_event(event)
            elif event["type"] == "end":
                event["processing_time"] = 0
                await send_event(event)

        # 保存AI回复到数据库
        if full_response:
            await message_service.save_message(
                db,
                session_id=message_data.session_id,
                role="assistant",
                content=full_response,
                metadata={
                    "intent": intent,
                    "sources": state.get("sources"),
                    "quick_actions": state.get("quick_actions"),
                    "recommended_products": state.get("recommended_products")
                }
            )

        # 更新会话活动时间
        await session_service.update_session_activity(db, message_data.session_id)

    return SSEResponse(handle_stream)


@router.get("/smart-questions")
async def get_smart_questions(
    mode: str = "fast",  # fast=快速规则, smart=AI生成
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取智能推荐的快速问题
    
    Args:
        mode: 生成模式
            - fast: 快速模式,基于规则生成(0.1秒)
            - smart: 智能模式,使用AI生成(3-5秒,有缓存)
    """
    try:
        # 获取最近订单(用于规则判断)
        from services.order_service import OrderService
        order_service = OrderService(db)
        recent_orders_result = await order_service.list_orders(user_id=user_id, page=1, page_size=5)
        recent_orders = recent_orders_result.get("items", [])
        
        # 转换订单格式
        order_data = []
        for order in recent_orders:
            order_data.append({
                "status": order.get("status"),
                "product_name": order.get("items", [{}])[0].get("product_title", "") if order.get("items") else "",
                "created_at": order.get("created_at")
            })
        
        # 快速模式: 基于规则生成(不调用AI)
        if mode == "fast":
            questions = smart_questions_service._get_rule_based_questions(order_data)
            return {"questions": questions, "mode": "fast"}
        
        # 智能模式: 使用AI生成(有缓存)
        user_profile = {}  # TODO: 从用户服务获取
        questions = await smart_questions_service.generate_smart_questions(
            user_id=user_id,
            user_profile=user_profile,
            recent_orders=order_data,
            browsing_history=None  # TODO: 添加浏览历史
        )
        
        return {"questions": questions, "mode": "smart"}
    
    except Exception as e:
        print(f"获取智能问题失败: {e}")
        # 返回基于规则的问题
        return {"questions": smart_questions_service._get_rule_based_questions(), "mode": "fallback"}

