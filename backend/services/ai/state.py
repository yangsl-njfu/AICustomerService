"""
Shared conversation state for workflow execution.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class ConversationState(TypedDict):
    # Request
    user_message: str
    user_id: str
    session_id: str
    business_id: Optional[str]
    execution_context: Optional[Dict[str, Any]]
    attachments: Optional[List[Dict]]

    # Context
    conversation_history: List[Dict[str, str]]
    user_profile: Dict[str, Any]

    # Processing
    intent: Optional[str]
    confidence: Optional[float]
    retrieved_docs: Optional[List[Dict]]
    tool_result: Optional[Any]
    tool_used: Optional[str]

    # Output
    response: str
    sources: Optional[List[Dict]]
    ticket_id: Optional[str]
    recommended_products: Optional[List[str]]
    quick_actions: Optional[List[Dict]]

    # Intent tracking
    intent_history: Optional[List[Dict[str, Any]]]
    conversation_summary: Optional[str]

    # Metadata
    timestamp: str
    processing_time: Optional[float]

    # Flow states
    purchase_flow: Optional[Dict[str, Any]]
    aftersales_flow: Optional[Dict[str, Any]]

    # Agent state
    topic_advisor_projects: Optional[List[Dict]]
    topic_advisor_tool_results: Optional[List[Dict]]
