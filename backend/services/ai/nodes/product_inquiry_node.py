"""
商品咨询节点
"""
import logging
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate
from database.connection import get_db_context
from services.product_service import ProductService

logger = logging.getLogger(__name__)


class ProductInquiryNode(BaseNode):
    """商品咨询节点"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行商品咨询"""
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
        
        # AI咨询
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是商品咨询专家。根据用户的问题，从所有商品中智能挑选最相关的3-5个商品进行详细介绍。

分析维度：
1. 关键词匹配: 用户提到的技术栈、专业、难度等
2. 语义理解: 理解用户真正想要什么
3. 质量优先: 优先推荐评分高、销量好的商品
4. 多样性: 提供不同价位、难度的选择

输出：
1. 回应用户问题
2. 介绍3-5个最相关的商品
3. 每个商品说明：为什么推荐、核心特点、技术栈、价格、适合谁
4. 必须包含商品ID"""),
            ("human", """用户问题：{question}

所有可选商品：
{products}

请智能分析并详细介绍最相关的商品（必须包含商品ID）：""")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages(
            question=state["user_message"],
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
            "label": "查看更多商品",
            "action": "view_more_products",
            "color": "primary"
        })
        
        state["quick_actions"] = quick_actions
        state["response"] = response.content
        state["recommended_products"] = recommended_ids
        
        return state
