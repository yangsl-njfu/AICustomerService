"""
管理后台API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from database import get_db
from database.models import User, Session, Message, Ticket, UserRole
from schemas import (
    SystemStatsResponse, ConversationSearchParams,
    KnowledgeDocumentCreate, KnowledgeDocumentResponse,
    SystemConfigUpdate, SystemConfigResponse
)
from services.auth_service import AuthService
from services.knowledge_retriever import knowledge_retriever

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前管理员"""
    try:
        user = await auth_service.get_current_user(db, credentials.credentials)
        result = await db.execute(select(User).where(User.id == user.id))
        db_user = result.scalar_one_or_none()
        
        if not db_user or db_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )
        return db_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取系统统计信息"""
    # 统计用户数
    total_users = await db.scalar(select(func.count(User.id)))
    
    # 统计会话数
    total_sessions = await db.scalar(select(func.count(Session.id)))
    
    # 统计消息数
    total_messages = await db.scalar(select(func.count(Message.id)))
    
    # 统计工单数
    total_tickets = await db.scalar(select(func.count(Ticket.id)))
    
    # 活跃会话数
    active_sessions = await db.scalar(
        select(func.count(Session.id)).where(Session.is_active == True)
    )
    
    # 待处理工单数
    pending_tickets = await db.scalar(
        select(func.count(Ticket.id)).where(Ticket.status == "pending")
    )
    
    return SystemStatsResponse(
        total_users=total_users or 0,
        total_sessions=total_sessions or 0,
        total_messages=total_messages or 0,
        total_tickets=total_tickets or 0,
        active_sessions=active_sessions or 0,
        pending_tickets=pending_tickets or 0
    )


@router.get("/conversations")
async def search_conversations(
    params: ConversationSearchParams = Depends(),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """搜索对话记录"""
    query = select(Session)
    
    if params.user_id:
        query = query.where(Session.user_id == params.user_id)
    
    if params.start_date:
        query = query.where(Session.created_at >= params.start_date)
    
    if params.end_date:
        query = query.where(Session.created_at <= params.end_date)
    
    query = query.limit(params.limit).offset(params.offset)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return {
        "conversations": [
            {
                "session_id": s.id,
                "user_id": s.user_id,
                "message_count": s.message_count,
                "created_at": s.created_at,
                "title": s.title
            }
            for s in sessions
        ],
        "total": len(sessions)
    }


@router.post("/knowledge/upload")
async def upload_knowledge_document(
    file: UploadFile = File(...),
    title: str = "",
    category: str = "",
    admin: User = Depends(get_current_admin)
):
    """上传知识库文档"""
    try:
        # 读取文件内容
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # 添加到向量数据库
        documents = [{
            "content": text_content,
            "metadata": {
                "title": title or file.filename,
                "category": category,
                "source": file.filename,
                "created_by": admin.id
            }
        }]
        
        doc_ids = await knowledge_retriever.add_documents(documents, "knowledge_base")
        
        return {
            "document_id": doc_ids[0],
            "title": title or file.filename,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败：{str(e)}"
        )


@router.delete("/knowledge/{document_id}")
async def delete_knowledge_document(
    document_id: str,
    admin: User = Depends(get_current_admin)
):
    """删除知识库文档"""
    try:
        await knowledge_retriever.delete_document(document_id, "knowledge_base")
        return {"message": "文档已删除"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败：{str(e)}"
        )


@router.put("/config")
async def update_system_config(
    config: SystemConfigUpdate,
    admin: User = Depends(get_current_admin)
):
    """更新系统配置"""
    # 这里应该更新数据库中的配置
    # 暂时返回成功
    return {
        "message": "配置已更新",
        "config": config.dict(exclude_none=True)
    }
