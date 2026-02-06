"""
收藏API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database.connection import get_db
from services.favorite_service import FavoriteService
from services.auth_service import AuthService


router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()


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
            status_code=401,
            detail=str(e)
        )


class FavoriteAdd(BaseModel):
    product_id: str


@router.post("/favorites")
async def add_favorite(
    favorite_data: FavoriteAdd,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """添加收藏"""
    service = FavoriteService(db)
    
    try:
        result = await service.add_favorite(
            user_id=user_id,
            product_id=favorite_data.product_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/favorites")
async def get_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取收藏列表"""
    service = FavoriteService(db)
    
    try:
        favorites = await service.get_favorites(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        return favorites
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/favorites/{product_id}")
async def remove_favorite(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """取消收藏"""
    service = FavoriteService(db)
    
    try:
        success = await service.remove_favorite(
            user_id=user_id,
            product_id=product_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="未收藏此商品")
        
        return {"message": "取消收藏成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/favorites/{product_id}/check")
async def check_favorite(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """检查是否已收藏"""
    service = FavoriteService(db)
    
    try:
        is_favorited = await service.is_favorited(
            user_id=user_id,
            product_id=product_id
        )
        return {"is_favorited": is_favorited}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
