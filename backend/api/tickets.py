"""
工单API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database import get_db
from schemas import TicketCreate, TicketUpdate, TicketResponse, TicketHistoryResponse
from services.auth_service import AuthService
from services.ticket_service import TicketService

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()
ticket_service = TicketService()


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


@router.post("", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建工单"""
    ticket = await ticket_service.create_ticket(db, user_id, ticket_data)
    return ticket


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取工单详情"""
    ticket = await ticket_service.get_ticket(db, ticket_id, user_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工单不存在"
        )
    return ticket


@router.get("", response_model=List[TicketResponse])
async def list_tickets(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的工单列表"""
    tickets = await ticket_service.list_user_tickets(db, user_id, status, limit, offset)
    return tickets


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    update_data: TicketUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """更新工单"""
    try:
        if update_data.status:
            ticket = await ticket_service.update_ticket_status(
                db,
                ticket_id,
                update_data.status,
                user_id,
                update_data.comment
            )
            return ticket
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供更新内容"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{ticket_id}/history", response_model=List[TicketHistoryResponse])
async def get_ticket_history(
    ticket_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取工单历史"""
    # 验证工单所有权
    ticket = await ticket_service.get_ticket(db, ticket_id, user_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工单不存在"
        )
    
    history = await ticket_service.get_ticket_history(db, ticket_id)
    return history
