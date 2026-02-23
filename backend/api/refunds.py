"""
售后退款API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.auth_service import AuthService
from services.refund_service import RefundService

router = APIRouter(prefix="/refunds")
security = HTTPBearer()
auth_service = AuthService()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    try:
        user = await auth_service.get_current_user(db, credentials.credentials)
        return user.id
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/")
async def list_refunds(
    page: int = 1,
    page_size: int = 20,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取用户售后列表"""
    service = RefundService(db)
    return await service.list_refunds(user_id, page, page_size)


@router.get("/{refund_id}")
async def get_refund(
    refund_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取售后详情"""
    service = RefundService(db)
    refund = await service.get_refund(refund_id)
    if not refund:
        raise HTTPException(status_code=404, detail="售后单不存在")
    return refund
