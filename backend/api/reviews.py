"""
评价API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
from database.connection import get_db
from services.review_service import ReviewService
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


class ReviewCreate(BaseModel):
    order_item_id: str
    rating: int
    content: Optional[str] = None
    images: Optional[List[str]] = None


class ReviewReply(BaseModel):
    reply: str


@router.post("/reviews")
async def create_review(
    review_data: ReviewCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """发表评价"""
    service = ReviewService(db)
    
    try:
        review = await service.create_review(
            order_item_id=review_data.order_item_id,
            buyer_id=current_user["id"],
            rating=review_data.rating,
            content=review_data.content,
            images=review_data.images
        )
        return review
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reviews")
async def get_reviews(
    product_id: Optional[str] = None,
    buyer_id: Optional[str] = None,
    seller_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取评价列表"""
    service = ReviewService(db)
    
    try:
        reviews = await service.get_reviews(
            product_id=product_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            page=page,
            page_size=page_size
        )
        return reviews
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reviews/{review_id}/reply")
async def reply_review(
    review_id: str,
    reply_data: ReviewReply,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """回复评价（卖家）"""
    service = ReviewService(db)
    
    try:
        review = await service.reply_review(
            review_id=review_id,
            seller_id=current_user["id"],
            reply=reply_data.reply
        )
        return review
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}/reviews")
async def get_product_reviews(
    product_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取商品的评价列表"""
    service = ReviewService(db)
    
    try:
        reviews = await service.get_reviews(
            product_id=product_id,
            page=page,
            page_size=page_size
        )
        return reviews
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
