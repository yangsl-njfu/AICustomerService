"""State machine for QA workflow."""
from __future__ import annotations

from enum import Enum


class QAFlowState(str, Enum):
    START = "start"
    QUICK_REPLY = "quick_reply"
    PREPARE = "prepare"
    RESPOND = "respond"
    END = "end"


PIPELINE_TRANSITIONS = {
    QAFlowState.START: QAFlowState.QUICK_REPLY,
    QAFlowState.QUICK_REPLY: QAFlowState.PREPARE,
    QAFlowState.PREPARE: QAFlowState.RESPOND,
    QAFlowState.RESPOND: QAFlowState.END,
}


def next_state(current: QAFlowState) -> QAFlowState:
    return PIPELINE_TRANSITIONS[current]
