"""State factory mixin for AIWorkflow."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

from ...state import ConversationState


class WorkflowStateMixin:
    """Conversation state construction helpers."""

    def _make_initial_state(
        self,
        user_id: str,
        session_id: str,
        message: str,
        attachments: Optional[list] = None,
        purchase_flow: Optional[Dict[str, Any]] = None,
        aftersales_flow: Optional[Dict[str, Any]] = None,
    ) -> ConversationState:
        execution_context = None
        business_id = None
        if self.runtime is not None:
            business_id = self.runtime.business_pack.business_id
            execution_context = asdict(
                self.runtime.build_context(
                    user_id=user_id,
                    session_id=session_id,
                    extra={"attachments": attachments or []},
                )
            )

        return {
            "user_message": message,
            "user_id": user_id,
            "session_id": session_id,
            "business_id": business_id,
            "execution_context": execution_context,
            "attachments": attachments or [],
            "conversation_history": [],
            "user_profile": {},
            "last_intent": None,
            "last_quick_actions": [],
            "active_task": None,
            "task_stack": [],
            "pending_question": None,
            "pending_action": None,
            "entry_classifier": None,
            "has_active_flow": False,
            "active_flow": None,
            "current_step": None,
            "expected_user_acts": [],
            "expected_slot": None,
            "expected_input_type": None,
            "semantic_source": None,
            "intent_hint": None,
            "semantic_confidence": None,
            "policy_action": None,
            "skill_route": None,
            "inflow_type": None,
            "flow_relation": None,
            "response_mode": None,
            "resume_mode": None,
            "dialogue_act": None,
            "domain_intent": None,
            "self_contained_request": False,
            "continue_previous_task": False,
            "need_clarification": False,
            "understanding_confidence": None,
            "slot_updates": {},
            "reference_resolution": None,
            "selected_quick_action": None,
            "intent": None,
            "confidence": None,
            "retrieved_docs": None,
            "tool_result": None,
            "tool_used": None,
            "response": "",
            "sources": None,
            "ticket_id": None,
            "recommended_products": None,
            "quick_actions": None,
            "timestamp": "",
            "processing_time": None,
            "intent_history": [],
            "conversation_summary": "",
            "purchase_flow": purchase_flow,
            "aftersales_flow": aftersales_flow,
            "topic_advisor_projects": [],
            "topic_advisor_tool_results": [],
        }
