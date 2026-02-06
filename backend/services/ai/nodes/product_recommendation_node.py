"""
商品推荐节点
"""
import logging
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate
from database.connection import get_db_context
from services.product_service import ProductService

logger = logging.getLogger(__name__)


class ProductRecommendationNode(BaseNode):
    """商品推荐节点"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行商品推荐"""
        # 获取商品
        async with get_db_context() as db:
            product_service = ProductService(db)
            result = await product_service.search_products(
                status="published",
                page=1,
                page_size=10,
                sort_by="rating",
                order="desc"
            )
            all_products = result.get("products", [])
        
        if not all_products:
            state["response"] = "抱歉，目前还没有可推荐的毕业设计作品。"
            return state
        
        # 构建商品信息
        products_info = []
        for i, p in enumerate(all_products, 1):
            price_yuan = p['price'] / 100
            rating_score = p['rating'] / 100
            product_info = f"""商品{i}: {p['title']}
技术栈: {', '.join(p.get('tech_stack', []))}
价格: ¥{price_yuan:.0f} | 评分: {rating_score:.1f}⭐ | 销量: {p.get('sales_count', 0)}
ID: {p['id']}"""
            products_info.append(product_info)
        
        products_text = "\n\n".join(products_info)
        
        # AI推荐
        recommend_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是毕业设计推荐专家。从商品中挑选3-5个最合适的推荐。

规则：
- "推荐"、"想要" → 推荐评分高、销量好的
- "Vue"、"Java"等技术栈 → 推荐对应技术的
- "前后端分离" → 推荐Vue+后端、React+后端等
- "便宜" → 推荐价格低的

输出：
1. 简短回应（1句话）
2. 推荐3-5个商品，每个说明：为什么推荐、特点、适合谁
3. 必须包含商品ID"""),
            ("human", """用户: {user_message}

商品:
{products}

推荐（包含ID）：""")
        ])
        
        response = await self.llm.ainvoke(recommend_prompt.format_messages(
            user_message=state["user_message"],
            products=products_text
        ))
        
        # 提取推荐的商品ID
        recommended_ids = []
        response_text = response.content
        
        for product in all_products:
            if product['id'] in response_text or product['title'] in response_text:
                recommended_ids.append(product['id'])
                if len(recommended_ids) >= 5:
                    break
        
        if not recommended_ids:
            recommended_ids = [p['id'] for p in all_products[:5]]
        
        # 生成快速按钮
        quick_actions = []
        for product_id in recommended_ids[:3]:
            product = next((p for p in all_products if p['id'] == product_id), None)
            if product:
                price_yuan = product['price'] / 100
                quick_actions.append({
                    "type": "product",
                    "label": product["title"],
                    "action": "view_product",
                    "data": {
                        "product_id": product["id"],
                        "price": price_yuan,
                        "title": product["title"]
                    },
                    "icon": "🎓"
                })
        
        quick_actions.append({
            "type": "button",
            "label": "查看全部推荐",
            "action": "view_all_recommendations",
            "color": "primary"
        })
        
        quick_actions.append({
            "type": "button",
            "label": "换一批推荐",
            "action": "refresh_recommendations",
            "icon": "🔄"
        })
        
        state["quick_actions"] = quick_actions
        state["response"] = response.content
        state["recommended_products"] = recommended_ids
        
        return state
