"""
个性化推荐节点
基于用户浏览历史进行推荐
"""
import logging
from .base import BaseNode
from ..state import ConversationState

logger = logging.getLogger(__name__)


class PersonalizedRecommendNode(BaseNode):
    """个性化推荐节点 - 基于用户浏览历史推荐"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行个性化推荐"""
        
        user_message = state.get("user_message", "")
        user_id = state.get("user_id")
        
        from database.connection import get_db_context
        from services.recommendation_service import RecommendationService
        from services.browse_service import BrowseService
        
        async with get_db_context() as db:
            browse_service = BrowseService(db)
            interests = await browse_service.get_user_interests(user_id=user_id)
            
            if not interests.get("tech_stack"):
                state["response"] = """您还没有浏览任何商品，快去商城看看有什么喜欢的吧！"""
                state["quick_actions"] = [
                    {
                        "type": "button",
                        "label": "去逛逛",
                        "action": "navigate",
                        "data": {"path": "/products"},
                        "icon": "🛍️"
                    }
                ]
                return state
            
            top_techs = [t["tech"] for t in interests.get("tech_stack", [])[:5]]
            
            rec_service = RecommendationService(db)
            recommendations = await rec_service.get_personalized_recommendations(
                user_id=user_id,
                limit=5
            )
            
            if not recommendations:
                state["response"] = "暂无可推荐商品，请先去逛逛商城~"
                state["quick_actions"] = [
                    {
                        "type": "button",
                        "label": "去逛逛",
                        "action": "navigate",
                        "data": {"path": "/products"},
                        "icon": "🛍️"
                    }
                ]
                return state
            
            product_cards = []
            for p in recommendations:
                product_cards.append({
                    "type": "product",
                    "data": {
                        "product_id": p.get("id"),
                        "title": p.get("title"),
                        "price": p.get("price"),
                        "rating": p.get("rating"),
                        "sales_count": p.get("sales_count"),
                        "tech_stack": p.get("tech_stack", []),
                        "description": ""
                    }
                })
            
            product_titles = [p.get("title") for p in recommendations[:3]]
            products_desc = "、".join(product_titles)
            
            prompt = f"""你是一个热情的电商客服。请为用户生成一句简短的推荐语（不超过30字），推荐以下商品：{products_desc}

要求：
- 语气亲切自然
- 不要提及技术栈或浏览历史
- 直接推荐商品，不要解释原因

示例：
- "为您精选了几个优质项目，快来看看吧！"
- "这些都是很受欢迎的作品，推荐给您~"
- "给您挑选了几个不错的毕设项目，看看有没有喜欢的"

请直接输出推荐语，不要其他内容："""
            
            try:
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=prompt)]
                response = await self.llm.ainvoke(messages)
                llm_response = response.content.strip()
                if llm_response and len(llm_response) < 50:
                    state["response"] = llm_response
                else:
                    state["response"] = "为您推荐以下商品："
            except Exception as e:
                logger.error(f"LLM生成推荐语失败: {e}")
                state["response"] = "为您推荐以下商品："
            
            state["quick_actions"] = product_cards + [
                {
                    "type": "button",
                    "label": "查看更多推荐",
                    "action": "navigate",
                    "data": {"path": "/products"},
                    "icon": "🔍"
                }
            ]
        
        return state
