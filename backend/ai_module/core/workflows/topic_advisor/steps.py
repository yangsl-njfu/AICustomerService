"""Composable node helpers for topic advisor workflow."""
from __future__ import annotations

from ...nodes.topic_advisor import (
    TopicAdvisorExecuteNode,
    TopicAdvisorRefineNode,
)
from ...state import ConversationState
from .contracts import TopicAdvisorMode
from .service import TopicAdvisorService


def build_mode_nodes(service: TopicAdvisorService):
    return {
        TopicAdvisorMode.DIRECT_RECOMMEND: TopicAdvisorExecuteNode(service),
        TopicAdvisorMode.REFINE_PREFERENCES: TopicAdvisorRefineNode(service),
    }


def cleanup_runtime_keys(state: ConversationState) -> ConversationState:
    state.pop("_topic_advisor_mode", None)
    return state
