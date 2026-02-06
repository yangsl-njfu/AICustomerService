"""
订单查询节点
"""
import logging
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate
from database.connection import get_db_context
from services.order_service import OrderService

logger = logging.getLogger(__name__)


class OrderQueryNode(BaseNode):
    """订单查询节点"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行订单查询"""
        # 检查是否已经通过Function Calling获取了订单信息
        tool_result = state.get("tool_result")
        orders_info = ""
        orders = []
        
        if tool_result:
            # 使用Function Calling的结果
            for result in tool_result:
                if result.get("tool") == "query_order":
                    order_data = result.get("result", {})
                    if order_data.get("success"):
                        orders.append(order_data)
                        orders_info += f"订单号：{order_data['order_no']}\n"
                        orders_info += f"总金额：¥{order_data['total_amount']}\n"
                        orders_info += f"状态：{order_data['status']}\n"
                        orders_info += f"创建时间：{order_data['created_at']}\n\n"
                elif result.get("tool") == "get_logistics":
                    logistics_data = result.get("result", {})
                    if logistics_data.get("success"):
                        orders_info += f"物流信息：{logistics_data.get('message', '')}\n"
                        orders_info += f"状态：{logistics_data.get('status', '')}\n\n"
        
        if not orders_info:
            # 如果没有Function Calling结果，手动查询
            async with get_db_context() as db:
                order_service = OrderService(db)
                result = await order_service.list_orders(
                    user_id=state["user_id"],
                    page=1,
                    page_size=5
                )
                orders = result.get("items", [])
            
            if not orders:
                state["response"] = "您还没有订单记录。浏览商品后可以下单购买哦！"
                return state
            
            # 构建订单信息
            orders_info = "\n\n".join([
                f"订单号：{o['order_no']}\n总金额：¥{o['total_amount']}\n状态：{o['status']}\n创建时间：{o['created_at']}"
                for o in orders
            ])
        
        # 生成快速按钮
        quick_actions = []
        if orders:
            for order in orders[:3]:
                order_no = order.get("order_no", "")
                if order_no:
                    quick_actions.append({
                        "type": "button",
                        "label": f"查看订单 {order_no}",
                        "action": "view_order",
                        "data": {"order_no": order_no},
                        "icon": "📦"
                    })
            
            quick_actions.append({
                "type": "button",
                "label": "查询物流",
                "action": "track_logistics",
                "icon": "🚚"
            })
            
            quick_actions.append({
                "type": "button",
                "label": "申请退款",
                "action": "request_refund",
                "icon": "💰"
            })
        
        state["quick_actions"] = quick_actions
        
        # 生成回复
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是订单查询助手。帮助用户了解订单状态。

订单状态说明：
- pending：待支付
- paid：已支付，等待卖家交付
- delivered：已交付，等待买家确认
- completed：已完成
- cancelled：已取消
- refunded：已退款

要求：
1. 根据用户问题提供订单信息
2. 解释订单状态
3. 如果有问题，提供解决建议
4. 语气友好、专业"""),
            ("human", """用户订单：
{orders}

用户问题：{question}

请回答：""")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages(
            orders=orders_info,
            question=state["user_message"]
        ))
        
        state["response"] = response.content
        return state
