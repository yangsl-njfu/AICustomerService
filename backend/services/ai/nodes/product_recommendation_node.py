"""
商品推荐节点
"""
import logging
from .base import BaseNode
from ..state import ConversationState

logger = logging.getLogger(__name__)


class ProductRecommendationNode(BaseNode):
    """商品推荐节点 - 根据用户需求推荐商品"""
    
    def __init__(self, llm=None):
        super().__init__(llm)
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行商品推荐 - 搜索并推荐商品"""
        
        user_message = state.get("user_message", "")
        tool_result = state.get("tool_result")
        
        products = []
        
        if tool_result:
            for tr in tool_result:
                logger.info(f"🔍 tool_result: tool={tr.get('tool')}, result_keys={tr.get('result', {}).keys()}")
                if tr.get("tool") == "search_products":
                    result = tr.get("result", {})
                    logger.info(f"🔍 search_products result: {result}")
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
            
            import re
            keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', user_message.lower())
            search_keyword = keywords[0] if keywords else None
            
            product_titles = [p.get("title") for p in products[:3]]
            products_desc = "、".join(product_titles)
            
            prompt = f"""用户说：「{user_message}」

你找到了以下商品：{products_desc}

请为用户生成一句简短的推荐语（不超过30字），语气亲切自然，直接推荐商品，不要提及技术栈或浏览历史。

示例：
- "为您找到了几个优质项目，快来看看吧！"
- "这些都是很受欢迎的作品，推荐给您~"
- "给您挑选了几个不错的项目，看看有没有喜欢的"

请直接输出推荐语，不要其他内容："""
            
            try:
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=prompt)]
                response = await self.llm.ainvoke(messages)
                llm_response = response.content.strip()
                
                if llm_response and len(llm_response) < 50:
                    state["response"] = llm_response
                else:
                    state["response"] = f"为您找到了 {len(products)} 个优质项目，快来看看吧！"
            except Exception as e:
                logger.warning(f"LLM生成推荐语失败: {e}")
                state["response"] = f"为您找到了 {len(products)} 个优质项目，快来看看吧！"
            
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
            
            for p in products[:3]:
                product_title = p.get('title', '')[:12]
                state["quick_actions"].append({
                    "type": "button",
                    "label": f"立即购买: {product_title}",
                    "action": "purchase_flow",
                    "data": {
                        "step": "confirm_product",
                        "product_id": p.get("id")
                    },
                    "icon": "💳"
                })
                state["quick_actions"].append({
                    "type": "button",
                    "label": f"加入购物车: {product_title}",
                    "action": "add_to_cart",
                    "data": {
                        "product_id": p.get("id"),
                        "product": p
                    },
                    "icon": "🛒"
                })
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
