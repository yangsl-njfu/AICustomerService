"""
路由决策
"""
from .state import ConversationState


class Router:
    """路由决策器"""
    
    def route_after_function_calling(self, state: ConversationState) -> str:
        """Function Calling后的路由决策"""
        intent = state.get("intent")
        tool_used = state.get("tool_used")
        
        # 商品推荐意图优先，即使调用了搜索工具也走推荐节点
        if intent == "商品推荐":
            return "product_recommendation"
        
        # 如果调用了工具，根据工具类型路由
        if tool_used:
            if "query_order" in tool_used or "get_logistics" in tool_used:
                return "order_query"
            elif "search_products" in tool_used:
                return "product_inquiry"
            elif "check_inventory" in tool_used or "calculate_price" in tool_used:
                return "purchase_guide"
        
        # 否则根据意图路由
        return self.route_by_intent(state)
    
    def route_by_intent(self, state: ConversationState) -> str:
        """根据意图路由"""
        if state.get("confidence", 0) < 0.6:
            return "clarify"

        intent_map = {
            "问答": "qa_flow",
            "工单": "ticket_flow",
            "产品咨询": "product_flow",
            "文档分析": "document_analysis",
            "商品推荐": "product_recommendation",
            "商品咨询": "product_inquiry",
            "购买指导": "purchase_guide",
            "订单查询": "order_query"
        }
        return intent_map.get(state.get("intent"), "clarify")
