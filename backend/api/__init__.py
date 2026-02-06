"""
API路由模块
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .chat import router as chat_router
from .tickets import router as tickets_router
from .files import router as files_router
from .admin import router as admin_router
from .knowledge import router as knowledge_router
from .products import router as products_router
from .cart import router as cart_router
from .orders import router as orders_router
from .reviews import router as reviews_router
from .favorites import router as favorites_router
from .gateway import router as gateway_router

# 创建主路由器
api_router = APIRouter(prefix="/api")

# 注册子路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(chat_router, prefix="/chat", tags=["对话"])
api_router.include_router(tickets_router, prefix="/tickets", tags=["工单"])
api_router.include_router(files_router, prefix="/files", tags=["文件"])
api_router.include_router(admin_router, prefix="/admin", tags=["管理"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["知识库"])

# 电商相关路由
api_router.include_router(products_router, tags=["商品"])
api_router.include_router(cart_router, tags=["购物车"])
api_router.include_router(orders_router, tags=["订单"])
api_router.include_router(reviews_router, tags=["评价"])
api_router.include_router(favorites_router, tags=["收藏"])

# API网关（多业务接入）
api_router.include_router(gateway_router, tags=["网关"])

__all__ = ["api_router"]
