"""
Function Calling工具系统
让AI能够主动调用数据库查询和业务功能
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class FunctionTool(ABC):
    """Function Tool基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict:
        """返回工具的参数schema（JSON Schema格式）"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        pass


class FunctionToolManager:
    """Function Tool管理器"""
    
    def __init__(self):
        self.tools: Dict[str, FunctionTool] = {}
    
    def register(self, tool: FunctionTool):
        """注册工具"""
        self.tools[tool.name] = tool
        logger.info(f"工具注册成功: {tool.name}")
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
        
        tool = self.tools[tool_name]
        logger.info(f"执行工具: {tool_name}, 参数: {kwargs}")
        try:
            result = await tool.execute(**kwargs)
            logger.info(f"工具执行成功: {tool_name}")
            return result
        except Exception as e:
            logger.error(f"工具执行失败: {tool_name}, 错误: {e}")
            raise
    
    def get_tools_schema(self) -> List[Dict]:
        """获取所有工具的schema"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.get_schema()
            }
            for tool in self.tools.values()
        ]
    
    def get_tool(self, tool_name: str) -> Optional[FunctionTool]:
        """获取指定工具"""
        return self.tools.get(tool_name)


# ==================== 核心工具实现 ====================

class QueryOrderTool(FunctionTool):
    """查询订单工具"""
    
    @property
    def name(self) -> str:
        return "query_order"
    
    @property
    def description(self) -> str:
        return "查询订单详情和状态。可以通过订单号查询订单信息、商品列表、支付状态等。"
    
    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "order_no": {
                    "type": "string",
                    "description": "订单号，格式如：ORD20240207123456"
                }
            },
            "required": ["order_no"]
        }
    
    async def execute(self, order_no: str) -> Dict:
        """执行订单查询"""
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


class SearchProductsTool(FunctionTool):
    """搜索商品工具"""
    
    @property
    def name(self) -> str:
        return "search_products"
    
    @property
    def description(self) -> str:
        return "搜索毕业设计商品。支持关键词搜索、价格筛选、难度筛选、技术栈筛选等。"
    
    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词，如：Vue、Python、管理系统"
                },
                "max_price": {
                    "type": "number",
                    "description": "最高价格（元）"
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["easy", "medium", "hard"],
                    "description": "难度等级：easy(简单)、medium(中等)、hard(困难)"
                },
                "tech_stack": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "技术栈列表，如：['Vue', 'Python', 'MySQL']"
                }
            },
            "required": ["keyword"]
        }
    
    async def execute(self, keyword: str, max_price: float = None, 
                     difficulty: str = None, tech_stack: List[str] = None) -> Dict:
        """执行商品搜索"""
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
                        "description": p.get("description", "")[:200]  # 限制描述长度
                    }
                    for p in products
                ]
            }


class GetUserInfoTool(FunctionTool):
    """获取用户信息工具"""
    
    @property
    def name(self) -> str:
        return "get_user_info"
    
    @property
    def description(self) -> str:
        return "获取用户基本信息，包括用户名、邮箱、注册时间等。"
    
    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                }
            },
            "required": ["user_id"]
        }
    
    async def execute(self, user_id: str) -> Dict:
        """执行用户信息查询"""
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


class CheckInventoryTool(FunctionTool):
    """检查库存工具"""
    
    @property
    def name(self) -> str:
        return "check_inventory"
    
    @property
    def description(self) -> str:
        return "检查商品库存状态。返回商品是否有货、库存数量等信息。"
    
    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "商品ID"
                }
            },
            "required": ["product_id"]
        }
    
    async def execute(self, product_id: str) -> Dict:
        """执行库存检查"""
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


class GetLogisticsTool(FunctionTool):
    """查询物流工具"""
    
    @property
    def name(self) -> str:
        return "get_logistics"
    
    @property
    def description(self) -> str:
        return "查询订单的物流信息。返回物流状态、物流公司、快递单号等。注意：数字商品通常没有物流信息。"
    
    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "order_no": {
                    "type": "string",
                    "description": "订单号"
                }
            },
            "required": ["order_no"]
        }
    
    async def execute(self, order_no: str) -> Dict:
        """执行物流查询"""
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


class CalculatePriceTool(FunctionTool):
    """计算价格工具"""
    
    @property
    def name(self) -> str:
        return "calculate_price"
    
    @property
    def description(self) -> str:
        return "计算商品总价。支持多个商品、优惠券等。返回原价、折扣、最终价格等信息。"
    
    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "商品ID列表"
                },
                "coupon_code": {
                    "type": "string",
                    "description": "优惠券代码（可选）"
                }
            },
            "required": ["product_ids"]
        }
    
    async def execute(self, product_ids: List[str], coupon_code: str = None) -> Dict:
        """执行价格计算"""
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


# ==================== 全局工具管理器 ====================

# 创建全局工具管理器实例
function_tool_manager = FunctionToolManager()

# 注册所有工具
function_tool_manager.register(QueryOrderTool())
function_tool_manager.register(SearchProductsTool())
function_tool_manager.register(GetUserInfoTool())
function_tool_manager.register(CheckInventoryTool())
function_tool_manager.register(GetLogisticsTool())
function_tool_manager.register(CalculatePriceTool())

logger.info(f"Function Tools初始化完成，共注册 {len(function_tool_manager.tools)} 个工具")
