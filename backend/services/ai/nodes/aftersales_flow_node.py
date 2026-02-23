"""
售后流程节点 - 处理退款/退货/换货全流程
流程: select_order → select_type → select_reason → input_description → confirm → submit → result
"""
import logging
from .base import BaseNode
from ..state import ConversationState

logger = logging.getLogger(__name__)

# 售后类型对应的可选原因
REASON_OPTIONS = {
    "refund_only": [
        ("quality_issue", "质量问题"),
        ("not_as_described", "与描述不符"),
        ("no_longer_needed", "不想要了"),
        ("other", "其他原因"),
    ],
    "return_refund": [
        ("quality_issue", "质量问题"),
        ("not_as_described", "与描述不符"),
        ("wrong_item", "发错商品"),
        ("missing_parts", "缺少部件"),
        ("other", "其他原因"),
    ],
    "exchange": [
        ("quality_issue", "质量问题"),
        ("wrong_item", "发错商品"),
        ("missing_parts", "缺少部件"),
        ("other", "其他原因"),
    ],
}

TYPE_LABELS = {
    "refund_only": "仅退款",
    "return_refund": "退货退款",
    "exchange": "换货",
}

REASON_LABELS = {
    "quality_issue": "质量问题",
    "not_as_described": "与描述不符",
    "wrong_item": "发错商品",
    "missing_parts": "缺少部件",
    "no_longer_needed": "不想要了",
    "other": "其他原因",
}

ORDER_STATUS_MAP = {
    "paid": "已支付", "delivered": "已送达", "completed": "已完成",
}


class AftersalesFlowNode(BaseNode):
    """售后流程节点"""

    async def execute(self, state: ConversationState) -> ConversationState:
        """执行售后流程"""
        flow = state.get("aftersales_flow", {})
        step = flow.get("step", "select_order") if flow else "select_order"

        logger.info(f"🔄 [AftersalesFlowNode] step={step}, flow_data={flow}")

        handlers = {
            "select_order": self.handle_select_order,
            "select_type": self.handle_select_type,
            "select_reason": self.handle_select_reason,
            "input_description": self.handle_input_description,
            "confirm": self.handle_confirm,
            "submit": self.handle_submit,
            "result": self.handle_result,
        }

        handler = handlers.get(step)
        if handler:
            return await handler(state, flow)

        state["response"] = "抱歉，售后流程出现了问题，请重新开始。"
        state["aftersales_flow"] = None
        return state

    async def handle_select_order(self, state: ConversationState, flow_data: dict):
        """步骤1: 展示可售后的订单列表"""
        from database.connection import get_db_context
        from services.refund_service import RefundService

        async with get_db_context() as db:
            service = RefundService(db)
            orders = await service.get_eligible_orders(state.get("user_id"))

        if not orders:
            state["response"] = "您暂时没有可以申请售后的订单。\n\n只有已支付、已送达或已完成的订单才能申请售后。"
            state["aftersales_flow"] = None
            state["quick_actions"] = [
                {"type": "button", "label": "查看我的订单", "action": "navigate",
                 "data": {"path": "/orders"}, "icon": "📦"},
            ]
            return state

        order_cards = []
        for order in orders[:5]:
            product_name = order["items"][0]["product_title"] if order["items"] else "商品"
            order_cards.append({
                "type": "order_card_simple",
                "label": product_name,
                "action": "aftersales_flow",
                "data": {
                    "step": "select_type",
                    "order_id": order["id"],
                    "order_no": order["order_no"],
                    "order_no": order["order_no"],
                    "status": order["status"],
                    "status_text": ORDER_STATUS_MAP.get(order["status"], order["status"]),
                    "product_name": product_name,
                    "total_amount": order["total_amount"] / 100,
                    "created_at": order["created_at"],
                    "items": order["items"],
                },
            })

        state["response"] = f"请选择需要售后的订单（共 {len(orders)} 个可售后订单）："
        state["quick_actions"] = order_cards
        state["aftersales_flow"] = {"step": "select_order"}
        return state

    async def handle_select_type(self, state: ConversationState, flow_data: dict):
        """步骤2: 选择售后类型"""
        order_id = flow_data.get("order_id")
        order_status = flow_data.get("status", "paid")

        if not order_id:
            state["response"] = "请先选择要售后的订单"
            return state

        product_name = flow_data.get("product_name", "商品")
        order_no = flow_data.get("order_no", "")

        state["aftersales_flow"] = {**flow_data, "step": "select_type"}

        buttons = []
        # 仅退款：未发货的订单可用
        if order_status in ("paid",):
            buttons.append({
                "type": "button", "label": "仅退款", "action": "aftersales_flow",
                "data": {**flow_data, "step": "select_reason", "refund_type": "refund_only"},
                "icon": "💰",
            })
        # 退货退款 & 换货：已发货/已完成的订单可用
        if order_status in ("delivered", "completed"):
            buttons.append({
                "type": "button", "label": "仅退款", "action": "aftersales_flow",
                "data": {**flow_data, "step": "select_reason", "refund_type": "refund_only"},
                "icon": "💰",
            })
            buttons.append({
                "type": "button", "label": "退货退款", "action": "aftersales_flow",
                "data": {**flow_data, "step": "select_reason", "refund_type": "return_refund"},
                "icon": "📦",
            })
            buttons.append({
                "type": "button", "label": "换货", "action": "aftersales_flow",
                "data": {**flow_data, "step": "select_reason", "refund_type": "exchange"},
                "icon": "🔄",
            })

        buttons.append({
            "type": "button", "label": "取消售后", "action": "aftersales_flow",
            "data": {"step": "cancel"}, "icon": "❌",
        })

        state["response"] = f"订单 {order_no} - {product_name}\n\n请选择售后类型："
        state["quick_actions"] = buttons
        return state

    async def handle_select_reason(self, state: ConversationState, flow_data: dict):
        """步骤3: 选择退款原因"""
        refund_type = flow_data.get("refund_type", "refund_only")
        type_label = TYPE_LABELS.get(refund_type, "售后")
        reasons = REASON_OPTIONS.get(refund_type, REASON_OPTIONS["refund_only"])

        state["aftersales_flow"] = {**flow_data, "step": "select_reason"}

        buttons = []
        for reason_key, reason_label in reasons:
            buttons.append({
                "type": "button", "label": reason_label, "action": "aftersales_flow",
                "data": {**flow_data, "step": "input_description", "reason": reason_key},
                "icon": "📝",
            })

        state["response"] = f"您选择了「{type_label}」，请选择原因："
        state["quick_actions"] = buttons
        return state

    async def handle_input_description(self, state: ConversationState, flow_data: dict):
        """步骤4: 补充问题描述"""
        reason = flow_data.get("reason", "other")
        reason_label = REASON_LABELS.get(reason, "其他")

        # 检查用户是否已经输入了描述（通过消息内容）
        user_msg = state.get("user_message", "").strip()
        has_description = user_msg and not user_msg.startswith("[售后流程]")

        if has_description:
            # 用户已输入描述，直接进入确认步骤
            flow_data["description"] = user_msg
            flow_data["step"] = "confirm"
            state["aftersales_flow"] = flow_data
            return await self.handle_confirm(state, flow_data)

        state["aftersales_flow"] = {**flow_data, "step": "input_description"}

        state["response"] = f"原因：{reason_label}\n\n您可以补充描述问题详情（直接输入文字发送），或跳过直接提交："
        state["quick_actions"] = [
            {
                "type": "button", "label": "跳过，直接确认", "action": "aftersales_flow",
                "data": {**flow_data, "step": "confirm", "description": None},
                "icon": "⏭️",
            },
        ]
        return state

    async def handle_confirm(self, state: ConversationState, flow_data: dict):
        """步骤5: 确认售后申请信息"""
        order_no = flow_data.get("order_no", "")
        product_name = flow_data.get("product_name", "商品")
        refund_type = flow_data.get("refund_type", "refund_only")
        reason = flow_data.get("reason", "other")
        description = flow_data.get("description", "")
        items = flow_data.get("items", [])

        # 计算退款金额（单位：分）
        if items:
            # items 中的 price 已经是分
            refund_amount = items[0].get("price", 0)
        else:
            # total_amount 是元，需要转换为分
            refund_amount = int(flow_data.get("total_amount", 0) * 100)

        flow_data["refund_amount"] = refund_amount
        state["aftersales_flow"] = {**flow_data, "step": "confirm"}

        type_label = TYPE_LABELS.get(refund_type, "售后")
        reason_label = REASON_LABELS.get(reason, "其他")
        amount_display = f"¥{refund_amount / 100:.2f}" if refund_type != "exchange" else "换货不涉及退款"

        response = f"""📋 售后申请确认

订单号：{order_no}
商品：{product_name}
售后类型：{type_label}
原因：{reason_label}
退款金额：{amount_display}"""
        if description:
            response += f"\n问题描述：{description}"
        response += "\n\n请确认以上信息："

        state["response"] = response
        state["quick_actions"] = [
            {
                "type": "button", "label": "确认提交", "action": "aftersales_flow",
                "data": {**flow_data, "step": "submit"},
                "icon": "✅",
            },
            {
                "type": "button", "label": "返回修改", "action": "aftersales_flow",
                "data": {**flow_data, "step": "select_type"},
                "icon": "✏️",
            },
        ]
        return state

    async def handle_submit(self, state: ConversationState, flow_data: dict):
        """步骤6: 提交售后申请 + 自动审核"""
        from database.connection import get_db_context
        from services.refund_service import RefundService

        user_id = state.get("user_id")
        order_id = flow_data.get("order_id")
        items = flow_data.get("items", [])
        order_item_id = items[0].get("id") if items else None

        async with get_db_context() as db:
            service = RefundService(db)

            # 创建售后申请
            refund = await service.create_refund_request(
                user_id=user_id,
                order_id=order_id,
                order_item_id=order_item_id,
                refund_type=flow_data.get("refund_type", "refund_only"),
                reason=flow_data.get("reason", "other"),
                description=flow_data.get("description"),
                evidence_images=flow_data.get("evidence_images"),
                refund_amount=flow_data.get("refund_amount", 0),
            )

            # 自动审核
            review_result = await service.auto_review(refund["id"])

        flow_data["refund_id"] = refund["id"]
        flow_data["refund_no"] = refund["refund_no"]
        flow_data["review_result"] = review_result
        flow_data["step"] = "result"
        state["aftersales_flow"] = flow_data

        return await self.handle_result(state, flow_data)

    async def handle_result(self, state: ConversationState, flow_data: dict):
        """步骤7: 展示售后结果"""
        refund_no = flow_data.get("refund_no", "")
        review_result = flow_data.get("review_result", {})
        approved = review_result.get("approved", False)
        review_reason = review_result.get("reason", "")
        refund_type = flow_data.get("refund_type", "refund_only")
        type_label = TYPE_LABELS.get(refund_type, "售后")

        if approved:
            if refund_type == "refund_only":
                response = f"""✅ 售后申请已通过，退款处理中！

售后单号：{refund_no}
类型：{type_label}
审核结果：{review_reason}

退款将在1-3个工作日内原路退回。"""
            else:
                response = f"""✅ 售后申请已通过！

售后单号：{refund_no}
类型：{type_label}
审核结果：{review_reason}

请将商品寄回，并在系统中填写退货快递单号。"""
        else:
            response = f"""📝 售后申请已提交，等待审核

售后单号：{refund_no}
类型：{type_label}
状态：待人工审核

我们会在1-2个工作日内完成审核，请耐心等待。"""

        state["response"] = response
        state["aftersales_flow"] = None  # 清空流程

        state["quick_actions"] = [
            {
                "type": "refund_card",
                "label": "售后详情",
                "action": "aftersales_flow",
                "data": {
                    "refund_no": refund_no,
                    "status": review_result.get("status", "pending"),
                    "status_text": "已通过" if approved else "待审核",
                    "refund_type_text": type_label,
                    "product_name": flow_data.get("product_name", "商品"),
                    "refund_amount": flow_data.get("refund_amount", 0) / 100,
                    "created_at": "",
                },
            },
            {"type": "button", "label": "查看我的订单", "action": "navigate",
             "data": {"path": "/orders"}, "icon": "📦"},
            {"type": "button", "label": "继续购物", "action": "navigate",
             "data": {"path": "/products"}, "icon": "🛒"},
        ]
        return state
