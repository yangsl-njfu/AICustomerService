"""技能路由器。

职责边界：
- 只在已经确定“需要调用业务能力”时工作
- 只决定选择哪个技能节点
- 不负责决定动作类型，也不负责恢复策略
"""
from __future__ import annotations

from .constants import DEFAULT_INTENT_HANDLER_MAP, INTENT_AFTERSALES, INTENT_RECOMMEND
from .state import ConversationState


class SkillRouter:
    """根据当前意图与工具结果选择具体技能。"""

    def __init__(self, runtime=None):
        self.runtime = runtime

    def route(self, state: ConversationState) -> str:
        intent = state.get("intent")
        tool_used = state.get("tool_used")

        if intent == INTENT_RECOMMEND:
            return "topic_advisor"

        if intent == INTENT_AFTERSALES:
            return "aftersales_flow"

        if tool_used:
            if "query_order" in tool_used or "get_logistics" in tool_used:
                return "order_query"
            if "search_products" in tool_used:
                return "product_inquiry"
            if "check_inventory" in tool_used or "calculate_price" in tool_used:
                return "purchase_guide"

        if self.runtime is not None:
            return self.runtime.get_handler_for_intent(intent)

        return DEFAULT_INTENT_HANDLER_MAP.get(intent, "clarify")
