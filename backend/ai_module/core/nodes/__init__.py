"""Lazy exports for AI workflow nodes.

Importing ``ai_module.core.nodes`` should not eagerly import every node and all of
their external dependencies.
"""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "BaseNode": (".common.base", "BaseNode"),
    "ContextNode": (".memory.context_node", "ContextNode"),
    "MessageEntryNode": (".understanding.message_entry_node", "MessageEntryNode"),
    "ResponsePlannerNode": (".policy.response_planner_node", "ResponsePlannerNode"),
    "ConversationControlNode": (".policy.conversation_control_node", "ConversationControlNode"),
    "TurnUnderstandingNode": (".understanding.turn_understanding_node", "TurnUnderstandingNode"),
    "PolicyNode": (".policy.policy_node", "PolicyNode"),
    "DialogueStateNode": (".policy.dialogue_state_node", "DialogueStateNode"),
    "IntentRecognitionNode": (".understanding.intent_node", "IntentRecognitionNode"),
    "FunctionCallingNode": (".policy.function_calling_node", "FunctionCallingNode"),
    "SaveContextNode": (".memory.save_context_node", "SaveContextNode"),
    "QANode": (".skills.qa_node", "QANode"),
    "DocumentNode": (".skills.document_node", "DocumentNode"),
    "TicketNode": (".skills.ticket_node", "TicketNode"),
    "ClarifyNode": (".skills.clarify_node", "ClarifyNode"),
    "CartInquiryNode": (".skills.cart_inquiry_node", "CartInquiryNode"),
    "DomainScopeGuardNode": (".skills.domain_scope_guard_node", "DomainScopeGuardNode"),
    "UnsupportedCapabilityNode": (".skills.unsupported_capability_node", "UnsupportedCapabilityNode"),
    "ProductInquiryNode": (".skills.product_inquiry_node", "ProductInquiryNode"),
    "OrderQueryNode": (".skills.order_query_node", "OrderQueryNode"),
    "PurchaseGuideNode": (".skills.purchase_guide_node", "PurchaseGuideNode"),
    "PurchaseFlowNode": (".skills.purchase_flow_node", "PurchaseFlowNode"),
    "AftersalesFlowNode": (".skills.aftersales_flow_node", "AftersalesFlowNode"),
    "TopicAdvisorNode": (".skills.topic_advisor_node", "TopicAdvisorNode"),
}


def __getattr__(name: str):
    module_name, attr_name = _EXPORTS.get(name, (None, None))
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name, __name__)
    return getattr(module, attr_name)


__all__ = list(_EXPORTS)

