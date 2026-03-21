"""State machine for topic advisor workflow."""
from __future__ import annotations

from enum import Enum


class TopicAdvisorState(str, Enum):
    START = "start"
    PREPARE = "prepare"
    RESOLVE_MODE = "resolve_mode"
    EXECUTE_MODE = "execute_mode"
    CLEANUP = "cleanup"
    END = "end"


PIPELINE_TRANSITIONS = {
    TopicAdvisorState.START: TopicAdvisorState.PREPARE,
    TopicAdvisorState.PREPARE: TopicAdvisorState.RESOLVE_MODE,
    TopicAdvisorState.RESOLVE_MODE: TopicAdvisorState.EXECUTE_MODE,
    TopicAdvisorState.EXECUTE_MODE: TopicAdvisorState.CLEANUP,
    TopicAdvisorState.CLEANUP: TopicAdvisorState.END,
}


def next_state(current: TopicAdvisorState) -> TopicAdvisorState:
    return PIPELINE_TRANSITIONS[current]
