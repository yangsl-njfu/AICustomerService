"""工作流路由决策。"""
from __future__ import annotations

from .constants import DEFAULT_INTENT_HANDLER_MAP, INTENT_AFTERSALES, INTENT_RECOMMEND
from .state import ConversationState


class Router:
    """根据意图和工具调用结果决定后续节点。"""

    def __init__(self, runtime=None):
        self.runtime = runtime

    def route_after_function_calling(self, state: ConversationState) -> str:
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

        return self.route_by_intent(state)

    def route_by_intent(self, state: ConversationState) -> str:
        if state.get("need_clarification"):
            return "clarify"

        if state.get("confidence", 0) < 0.6:
            return "clarify"

        if self.runtime is not None:
            return self.runtime.get_handler_for_intent(state.get("intent"))

        return DEFAULT_INTENT_HANDLER_MAP.get(state.get("intent"), "clarify")
