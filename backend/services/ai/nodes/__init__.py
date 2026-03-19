"""Lazy exports for AI workflow nodes.

Importing ``services.ai.nodes`` should not eagerly import every node and all of
their external dependencies.
"""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "BaseNode": (".base", "BaseNode"),
    "ContextNode": (".context_node", "ContextNode"),
    "MessageEntryNode": (".message_entry_node", "MessageEntryNode"),
    "ResponsePlannerNode": (".response_planner_node", "ResponsePlannerNode"),
    "ConversationControlNode": (".conversation_control_node", "ConversationControlNode"),
    "TurnUnderstandingNode": (".turn_understanding_node", "TurnUnderstandingNode"),
    "PolicyNode": (".policy_node", "PolicyNode"),
    "DialogueStateNode": (".dialogue_state_node", "DialogueStateNode"),
    "IntentRecognitionNode": (".intent_node", "IntentRecognitionNode"),
    "FunctionCallingNode": (".function_calling_node", "FunctionCallingNode"),
    "SaveContextNode": (".save_context_node", "SaveContextNode"),
    "QANode": (".qa_node", "QANode"),
    "DocumentNode": (".document_node", "DocumentNode"),
    "TicketNode": (".ticket_node", "TicketNode"),
    "ClarifyNode": (".clarify_node", "ClarifyNode"),
    "ProductInquiryNode": (".product_inquiry_node", "ProductInquiryNode"),
    "OrderQueryNode": (".order_query_node", "OrderQueryNode"),
    "PurchaseGuideNode": (".purchase_guide_node", "PurchaseGuideNode"),
    "PurchaseFlowNode": (".purchase_flow_node", "PurchaseFlowNode"),
    "AftersalesFlowNode": (".aftersales_flow_node", "AftersalesFlowNode"),
    "TopicAdvisorNode": (".topic_advisor_node", "TopicAdvisorNode"),
}


def __getattr__(name: str):
    module_name, attr_name = _EXPORTS.get(name, (None, None))
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name, __name__)
    return getattr(module, attr_name)


__all__ = list(_EXPORTS)
