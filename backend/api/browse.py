"""
浏览历史API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List
from database.connection import get_db
from services.auth_service import AuthService
from services.browse_service import BrowseService
from services.recommendation_service import RecommendationService


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


class BrowseRecord(BaseModel):
    product_id: str
    view_duration: int = 0


@router.get("/recommendations")
async def get_personalized_recommendations(
    limit: int = Query(10, ge=1, le=20),
    exclude_ids: str = Query(None, description="排除的商品ID，逗号分隔"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取个性化推荐"""
    service = RecommendationService(db)
    
    exclude_list = []
    if exclude_ids:
        exclude_list = [pid.strip() for pid in exclude_ids.split(",") if pid.strip()]
    
    try:
        recommendations = await service.get_personalized_recommendations(
            user_id=user_id,
            limit=limit,
            exclude_ids=exclude_list
        )
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/similar/{product_id}")
async def get_similar_products(
    product_id: str,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """获取相似商品"""
    service = RecommendationService(db)
    
    try:
        similar = await service.get_similar_products(
            product_id=product_id,
            limit=limit
        )
        return {"similar_products": similar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/browse")
async def record_browse(
    browse_data: BrowseRecord,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """记录浏览历史"""
    service = BrowseService(db)
    
    try:
        result = await service.record_browse(
            user_id=user_id,
            product_id=browse_data.product_id,
            view_duration=browse_data.view_duration
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/browse")
async def get_browse_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取浏览历史"""
    service = BrowseService(db)
    
    try:
        result = await service.get_browse_history(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/browse/interests")
async def get_user_interests(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取用户兴趣标签"""
    service = BrowseService(db)
    
    try:
        result = await service.get_user_interests(user_id=user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/browse/{product_id}")
async def delete_browse_record(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """删除浏览记录"""
    service = BrowseService(db)
    
    try:
        await service.delete_browse_record(user_id=user_id, product_id=product_id)
        return {"message": "删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/browse")
async def clear_browse_history(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """清空浏览历史"""
    service = BrowseService(db)
    
    try:
        await service.clear_browse_history(user_id=user_id)
        return {"message": "清空成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
