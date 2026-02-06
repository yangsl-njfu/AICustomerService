"""
购买指导节点
"""
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate


class PurchaseGuideNode(BaseNode):
    """购买指导节点"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行购买指导"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是购买指导专家。帮助用户了解购买流程。

平台购买流程：
1. 浏览商品，选择心仪的毕业设计作品
2. 点击"加入购物车"或"立即购买"
3. 在购物车中确认商品和价格
4. 点击"去结算"，填写订单信息
5. 选择支付方式（支持支付宝、微信支付）
6. 完成支付后，卖家会交付商品文件
7. 确认收货后可以评价

支付方式：
- 支付宝
- 微信支付

退款政策：
- 商品交付前可以取消订单，全额退款
- 商品交付后，如有质量问题可申请退款
- 退款会在3-5个工作日内到账

要求：
1. 根据用户问题提供相应指导
2. 语言简洁明了
3. 如果用户遇到具体问题，建议创建工单"""),
            ("human", "用户问题：{question}\n\n请提供购买指导：")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages(
            question=state["user_message"]
        ))
        
        state["response"] = response.content
        return state
