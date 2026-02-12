"""
商品推荐节点
"""
import logging
from .base import BaseNode
from ..state import ConversationState

logger = logging.getLogger(__name__)


class ProductRecommendationNode(BaseNode):
    """商品推荐节点 - 根据用户需求推荐商品"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行商品推荐 - 搜索并推荐商品"""
        
        user_message = state.get("user_message", "")
        tool_result = state.get("tool_result")
        
        products = []
        
        if tool_result:
            for tr in tool_result:
                if tr.get("tool") == "search_products":
                    result = tr.get("result", {})
                    if result.get("success"):
                        products = result.get("products", [])
        
        if not products:
            from database.connection import get_db_context
            from services.product_service import ProductService
            
            import re
            keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', user_message.lower())
            search_keyword = keywords[0] if keywords else None
            
            async with get_db_context() as db:
                product_service = ProductService(db)
                
                if search_keyword:
                    result = await product_service.search_products(
                        keyword=search_keyword,
                        status="published",
                        page=1,
                        page_size=5,
                        sort_by="rating",
                        order="desc"
                    )
                    products = result.get("products", [])
                
                if not products:
                    result = await product_service.search_products(
                        status="published",
                        page=1,
                        page_size=5,
                        sort_by="sales_count",
                        order="desc"
                    )
                    products = result.get("products", [])
        
        if products:
            product_cards = []
            for p in products[:5]:
                product_cards.append({
                    "type": "product",
                    "data": {
                        "product_id": p.get("id"),
                        "title": p.get("title"),
                        "price": p.get("price"),
                        "rating": p.get("rating"),
                        "sales_count": p.get("sales_count"),
                        "tech_stack": p.get("tech_stack", []),
                        "description": p.get("description", "")[:150]
                    }
                })
            
            tech_set = set()
            for p in products:
                for t in p.get("tech_stack", []):
                    tech_set.add(t)
            tech_str = "、".join(list(tech_set)[:5]) if tech_set else "各类技术"
            
            import re
            keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', user_message.lower())
            search_keyword = keywords[0] if keywords else None
            
            if search_keyword and any(search_keyword.lower() in t.lower() or t.lower() in search_keyword.lower() for p in products for t in p.get("tech_stack", [])):
                response_prefix = f"根据「{search_keyword}」为您找到以下商品："
            else:
                response_prefix = f"未找到完全匹配的商品，为您推荐以下热门商品："
            
            state["response"] = f"""{response_prefix}

共 {len(products)} 个商品，涵盖 {tech_str} 等技术栈。"""
            
            state["quick_actions"] = product_cards + [
                {
                    "type": "button",
                    "label": "查看更多商品",
                    "action": "navigate",
                    "data": {"path": "/products"},
                    "icon": "🔍"
                },
                {
                    "type": "button",
                    "label": "查看我的订单",
                    "action": "send_question",
                    "data": {"question": "查看我的订单"},
                    "icon": "📦"
                }
            ]
        else:
            state["response"] = """抱歉，暂时没有找到符合您需求的商品。

不过别担心，我可以为您推荐一些热门商品！"""

            state["quick_actions"] = [
                {
                    "type": "button",
                    "label": "查看热门商品",
                    "action": "send_question",
                    "data": {"question": "推荐热门项目"},
                    "icon": "🔥"
                },
                {
                    "type": "button",
                    "label": "前往商城",
                    "action": "navigate",
                    "data": {"path": "/products"},
                    "icon": "🛍️"
                }
            ]
        
        return state
