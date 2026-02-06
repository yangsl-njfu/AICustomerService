"""
购物车API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database.connection import get_db
from services.cart_service import CartService
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


class CartItemAdd(BaseModel):
    product_id: str
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


@router.get("/cart")
async def get_cart(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取购物车"""
    service = CartService(db)
    
    try:
        cart = await service.get_cart(user_id)
        return cart
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cart")
async def add_to_cart(
    item: CartItemAdd,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """添加商品到购物车或更新数量"""
    service = CartService(db)
    
    try:
        result = await service.add_to_cart(user_id, item.product_id, item.quantity)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cart/{product_id}")
async def update_cart_item(
    product_id: str,
    item: CartItemUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """更新购物车商品数量"""
    service = CartService(db)
    
    try:
        result = await service.update_quantity(user_id, product_id, item.quantity)
        
        if not result:
            raise HTTPException(status_code=404, detail="购物车中没有此商品")
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cart/{product_id}")
async def remove_from_cart(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """从购物车删除商品"""
    service = CartService(db)
    
    try:
        success = await service.remove_from_cart(user_id, product_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="购物车中没有此商品")
        
        return {"message": "删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cart")
async def clear_cart(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """清空购物车"""
    service = CartService(db)
    
    try:
        await service.clear_cart(user_id)
        return {"message": "购物车已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cart/count")
async def get_cart_count(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取购物车商品数量"""
    service = CartService(db)
    
    try:
        count = await service.get_cart_count(user_id)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
