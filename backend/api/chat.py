"""
对话API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json

from database import get_db
from schemas import (
    SessionCreate, SessionResponse, MessageCreate, 
    MessageResponse, ConversationResponse
)
from services.auth_service import AuthService
from services.session_service import SessionService
from services.message_service import MessageService
from services.langgraph_workflow import langgraph_workflow
from services.attachment_service import AttachmentService

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
    result = await langgraph_workflow.process_message(
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
        processing_time=result.get("processing_time")
    )


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
    
    async def event_generator():
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
        yield f"data: {json.dumps({'type': 'start'})}\n\n"
        
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
        
        # 流式处理消息 - 实时生成内容
        full_response = ""
        intent = None
        sources = None
        
        async for chunk in langgraph_workflow.process_message_stream(
            user_id=user_id,
            session_id=message_data.session_id,
            message=message_data.message,
            attachments=attachment_info
        ):
            if chunk["type"] == "intent":
                intent = chunk.get("intent")
                yield f"data: {json.dumps(chunk)}\n\n"
            elif chunk["type"] == "content":
                full_response += chunk.get("delta", "")
                yield f"data: {json.dumps(chunk)}\n\n"
            elif chunk["type"] == "end":
                sources = chunk.get("sources")
                yield f"data: {json.dumps(chunk)}\n\n"
        
        # 保存AI回复到数据库
        if full_response:
            await message_service.save_message(
                db,
                session_id=message_data.session_id,
                role="assistant",
                content=full_response,
                metadata={"intent": intent, "sources": sources}
            )
        
        # 更新会话活动时间
        await session_service.update_session_activity(db, message_data.session_id)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
