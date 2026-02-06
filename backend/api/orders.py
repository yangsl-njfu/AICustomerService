"""
订单API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from database.connection import get_db
from services.order_service import OrderService
from services.payment_service import PaymentService
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


class OrderCreate(BaseModel):
    product_ids: List[str]


class OrderPay(BaseModel):
    payment_method: str


@router.post("/orders")
async def create_order(
    order_data: OrderCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建订单"""
    service = OrderService(db)
    
    try:
        order = await service.create_order(
            buyer_id=user_id,
            product_ids=order_data.product_ids
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取订单列表"""
    service = OrderService(db)
    
    try:
        orders = await service.list_orders(
            user_id=user_id,
            status=status,
            page=page,
            page_size=page_size
        )
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取订单详情"""
    service = OrderService(db)
    
    order = await service.get_order(order_id, user_id=user_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    return order


@router.post("/orders/{order_id}/pay")
async def pay_order(
    order_id: str,
    pay_data: OrderPay,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """支付订单"""
    try:
        # 创建支付服务
        payment_service = PaymentService(db)
        order_service = OrderService(db)
        
        # 创建支付
        payment = await payment_service.create_payment(
            order_id=order_id,
            payment_method=pay_data.payment_method
        )
        
        # 模拟支付处理
        result = await payment_service.process_payment(payment["transaction_id"])
        
        # 获取更新后的订单
        updated_order = await order_service.get_order(order_id, user_id=user_id)
        
        # 返回支付结果
        return {
            "success": result["success"],
            "message": result["message"],
            "order": updated_order
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"支付错误: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """取消订单"""
    service = OrderService(db)
    
    try:
        success = await service.cancel_order(order_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        # 获取更新后的订单
        updated_order = await service.get_order(order_id, user_id=user_id)
        
        return {"message": "订单已取消", "order": updated_order}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/{order_id}/deliver")
async def deliver_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """交付订单（卖家）"""
    service = OrderService(db)
    
    try:
        order = await service.update_order_status(order_id, "delivered")
        
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        return {"message": "订单已交付", "order": order}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/{order_id}/complete")
async def complete_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """确认收货（买家）"""
    service = OrderService(db)
    
    try:
        order = await service.update_order_status(
            order_id,
            "completed",
            user_id=user_id
        )
        
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        return {"message": "订单已完成", "order": order}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 卖家订单管理
@router.get("/seller/orders")
async def get_seller_orders(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取卖家订单列表"""
    service = OrderService(db)
    
    try:
        orders = await service.list_orders(
            seller_id=user_id,
            status=status,
            page=page,
            page_size=page_size
        )
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
