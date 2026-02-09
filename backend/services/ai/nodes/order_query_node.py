"""
订单查询节点
"""
import logging
from .base import BaseNode
from ..state import ConversationState
from database.connection import get_db_context
from services.order_service import OrderService

logger = logging.getLogger(__name__)


class OrderQueryNode(BaseNode):
    """订单查询节点 - 让用户选择订单"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行订单查询 - 让用户选择订单或处理具体订单"""
        user_message = state["user_message"].lower()
        
        # 检查用户是否提到了具体订单号
        import re
        order_no_pattern = r'ORD\d{14}[A-Z0-9]{6}'
        order_no_match = re.search(order_no_pattern, state["user_message"], re.IGNORECASE)
        
        if order_no_match:
            # 用户选择了具体订单，查询该订单详情
            order_no = order_no_match.group(0).upper()
            
            async with get_db_context() as db:
                order_service = OrderService(db)
                # 查询具体订单
                result = await order_service.list_orders(
                    user_id=state["user_id"],
                    page=1,
                    page_size=100
                )
                orders = result.get("items", [])
                
                # 找到匹配的订单
                target_order = None
                for order in orders:
                    if order.get("order_no") == order_no:
                        target_order = order
                        break
                
                if not target_order:
                    state["response"] = f"抱歉，没有找到订单号 {order_no}。请确认订单号是否正确。"
                    return state
                
                # 构建订单详情
                status_map = {
                    "pending": "待支付",
                    "paid": "已支付",
                    "shipped": "已发货",
                    "delivered": "已送达",
                    "completed": "已完成",
                    "cancelled": "已取消"
                }
                status_text = status_map.get(target_order.get("status"), "未知")
                total_amount = target_order.get("total_amount", 0) / 100
                created_at = target_order.get("created_at", "")
                
                # 获取商品信息
                items = target_order.get("items", [])
                product_info = ""
                if items:
                    product_info = "\n".join([f"- {item.get('product_title', '商品')}" for item in items])
                
                state["response"] = f"""好的，为您查询订单 {order_no}：

**订单状态**: {status_text}
**订单金额**: ¥{total_amount:.2f}
**下单时间**: {created_at}
**商品清单**:
{product_info}

请问您需要什么帮助？"""
                
                # 根据订单状态提供不同的快速操作
                quick_actions = []
                
                if target_order.get("status") == "shipped":
                    quick_actions.append({
                        "type": "button",
                        "label": "查看物流信息",
                        "action": "send_question",
                        "data": {"question": f"查看订单 {order_no} 的物流信息"},
                        "icon": "🚚"
                    })
                elif target_order.get("status") == "pending":
                    quick_actions.append({
                        "type": "button",
                        "label": "去支付",
                        "action": "navigate",
                        "data": {"path": f"/orders"},
                        "icon": "💰"
                    })
                elif target_order.get("status") in ["completed", "delivered"]:
                    quick_actions.append({
                        "type": "button",
                        "label": "申请退款",
                        "action": "send_question",
                        "data": {"question": f"我要申请退款，订单号 {order_no}"},
                        "icon": "💰"
                    })
                
                quick_actions.extend([
                    {
                        "type": "button",
                        "label": "联系卖家",
                        "action": "send_question",
                        "data": {"question": "如何联系卖家?"},
                        "icon": "💬"
                    },
                    {
                        "type": "button",
                        "label": "查看其他订单",
                        "action": "open_order_selector",
                        "data": {},
                        "icon": "📋"
                    }
                ])
                
                state["quick_actions"] = quick_actions
                return state
        
        # 用户没有选择具体订单，显示订单列表
        async with get_db_context() as db:
            order_service = OrderService(db)
            result = await order_service.list_orders(
                user_id=state["user_id"],
                page=1,
                page_size=10
            )
            orders = result.get("items", [])
        
        if not orders:
            state["response"] = "您还没有订单记录。如果您想购买商品，可以前往商城首页浏览。"
            state["quick_actions"] = [
                {
                    "type": "button",
                    "label": "前往商城首页",
                    "action": "navigate",
                    "data": {"path": "/products"},
                    "icon": "🏠",
                    "color": "primary"
                }
            ]
            return state
        
        # 生成订单选择按钮（不显示订单列表，只显示选择按钮）
        state["response"] = f"您好！您有 {len(orders)} 个订单，请点击下方按钮选择您要咨询的订单："
        
        # 只添加一个"选择订单"按钮，点击后弹出订单选择弹窗
        quick_actions = [{
            "type": "button",
            "label": "📋 选择订单",
            "action": "open_order_selector",
            "data": {},
            "icon": "📋"
        }]
        
        logger.info(f"生成订单选择按钮")
        state["quick_actions"] = quick_actions
        return state
