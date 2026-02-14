"""
Function Calling工具系统
让AI能够主动调用数据库查询和业务功能
"""
import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# ==================== LangChain @tool 装饰器工具定义 ====================


@tool
async def query_order(order_no: str) -> dict:
    """查询订单详情和状态。可以通过订单号查询订单信息、商品列表、支付状态等。

    Args:
        order_no: 订单号，格式如：ORD20240207123456
    """
    from database.connection import get_db_context
    from services.order_service import OrderService

    async with get_db_context() as db:
        order_service = OrderService(db)
        order = await order_service.get_order_by_no(order_no)

        if not order:
            return {
                "success": False,
                "error": "订单不存在",
                "order_no": order_no
            }

        return {
            "success": True,
            "order_no": order["order_no"],
            "status": order["status"],
            "total_amount": float(order["total_amount"]),
            "created_at": str(order["created_at"]),
            "items": order.get("items", []),
            "buyer_name": order.get("buyer_name", ""),
            "buyer_phone": order.get("buyer_phone", "")
        }


@tool
async def search_products(keyword: str, max_price: float = None,
                          difficulty: str = None, tech_stack: list[str] = None) -> dict:
    """搜索毕业设计商品。支持关键词搜索、价格筛选、难度筛选、技术栈筛选等。

    Args:
        keyword: 搜索关键词，如：Vue、Python、管理系统
        max_price: 最高价格（元）
        difficulty: 难度等级：easy(简单)、medium(中等)、hard(困难)
        tech_stack: 技术栈列表，如：['Vue', 'Python', 'MySQL']
    """
    from database.connection import get_db_context
    from services.product_service import ProductService

    async with get_db_context() as db:
        product_service = ProductService(db)

        # 构建搜索参数
        filters = {
            "keyword": keyword,
            "status": "published",
            "page": 1,
            "page_size": 5
        }

        if max_price:
            filters["max_price"] = max_price
        if difficulty:
            filters["difficulty"] = difficulty
        if tech_stack:
            filters["tech_stack"] = tech_stack

        result = await product_service.search_products(**filters)
        products = result.get("products", [])

        return {
            "success": True,
            "total": len(products),
            "products": [
                {
                    "id": p["id"],
                    "title": p["title"],
                    "price": float(p["price"]),
                    "rating": float(p["rating"]),
                    "sales_count": p["sales_count"],
                    "tech_stack": p.get("tech_stack", []),
                    "difficulty": p.get("difficulty", ""),
                    "description": p.get("description", "")[:200]
                }
                for p in products
            ]
        }


@tool
async def get_user_info(user_id: str) -> dict:
    """获取用户基本信息，包括用户名、邮箱、注册时间等。

    Args:
        user_id: 用户ID
    """
    from database.connection import get_db_context
    from database.models import User
    from sqlalchemy import select

    async with get_db_context() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return {
                "success": False,
                "error": "用户不存在"
            }

        return {
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": str(user.created_at)
        }


@tool
async def check_inventory(product_id: str) -> dict:
    """检查商品库存状态。返回商品是否有货、库存数量等信息。

    Args:
        product_id: 商品ID
    """
    from database.connection import get_db_context
    from services.product_service import ProductService

    async with get_db_context() as db:
        product_service = ProductService(db)
        product = await product_service.get_product(product_id)

        if not product:
            return {
                "success": False,
                "error": "商品不存在"
            }

        # 对于数字商品，库存通常是无限的
        # 这里简化处理，实际可以根据业务需求调整
        stock = product.get("stock", 999)
        in_stock = stock > 0

        return {
            "success": True,
            "product_id": product_id,
            "product_title": product["title"],
            "in_stock": in_stock,
            "stock": stock,
            "status": product["status"]
        }


@tool
async def get_logistics(order_no: str) -> dict:
    """查询订单的物流信息。返回物流状态、物流公司、快递单号等。注意：数字商品通常没有物流信息。

    Args:
        order_no: 订单号
    """
    from database.connection import get_db_context
    from services.order_service import OrderService

    async with get_db_context() as db:
        order_service = OrderService(db)
        order = await order_service.get_order_by_no(order_no)

        if not order:
            return {
                "success": False,
                "error": "订单不存在"
            }

        # 对于数字商品，通常是在线交付，没有传统物流
        # 这里返回交付状态
        status = order["status"]

        if status == "delivered":
            return {
                "success": True,
                "order_no": order_no,
                "delivery_type": "digital",
                "message": "数字商品已在线交付，请在订单详情中查看下载链接。",
                "status": "已交付"
            }
        elif status == "paid":
            return {
                "success": True,
                "order_no": order_no,
                "delivery_type": "digital",
                "message": "订单已支付，卖家正在准备交付文件。",
                "status": "准备中"
            }
        else:
            return {
                "success": True,
                "order_no": order_no,
                "delivery_type": "digital",
                "message": f"订单状态：{status}",
                "status": status
            }


@tool
async def calculate_price(product_ids: list[str], coupon_code: str = None) -> dict:
    """计算商品总价。支持多个商品、优惠券等。返回原价、折扣、最终价格等信息。

    Args:
        product_ids: 商品ID列表
        coupon_code: 优惠券代码（可选）
    """
    from database.connection import get_db_context
    from services.product_service import ProductService

    async with get_db_context() as db:
        product_service = ProductService(db)

        total_price = 0.0
        products_info = []

        for product_id in product_ids:
            product = await product_service.get_product(product_id)
            if product:
                price = float(product["price"])
                total_price += price
                products_info.append({
                    "id": product_id,
                    "title": product["title"],
                    "price": price
                })

        # 简化处理：暂不实现优惠券逻辑
        discount = 0.0
        if coupon_code:
            # TODO: 实现优惠券验证和折扣计算
            pass

        final_price = total_price - discount

        return {
            "success": True,
            "products": products_info,
            "original_price": total_price,
            "discount": discount,
            "final_price": final_price,
            "coupon_applied": coupon_code if discount > 0 else None
        }


@tool
async def get_personalized_recommendations(user_id: str, limit: int = 5) -> dict:
    """基于用户浏览历史获取个性化商品推荐。该工具会分析用户近期浏览过的商品，根据技术栈偏好推荐相关商品。

    Args:
        user_id: 用户的唯一标识ID
        limit: 返回推荐商品数量，默认5个
    """
    print(f"🎯 [get_personalized_recommendations] user_id={user_id}, limit={limit}", flush=True)
    from database.connection import get_db_context
    from services.recommendation_service import RecommendationService

    async with get_db_context() as db:
        rec_service = RecommendationService(db)
        
        recommendations = await rec_service.get_personalized_recommendations(
            user_id=user_id,
            limit=limit
        )
        
        if not recommendations:
            popular = await rec_service.get_popular_products(limit=limit)
            return {
                "success": True,
                "message": "暂无个性化推荐，为您推荐热门商品",
                "products": popular,
                "is_popular": True
            }
        
        return {
            "success": True,
            "message": "为您推荐以下商品",
            "products": recommendations,
            "is_personalized": True
        }


# ==================== LangChain 工具列表 ====================

all_tools = [query_order, search_products, get_user_info,
             check_inventory, get_logistics, calculate_price,
             get_personalized_recommendations]
