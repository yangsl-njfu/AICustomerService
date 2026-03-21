"""State machine for aftersales workflow orchestration."""
from __future__ import annotations

from enum import Enum


class AftersalesFlowState(str, Enum):
    START = "start"
    VALIDATE_FLOW = "validate_flow"
    RESOLVE_STEP = "resolve_step"
    RUN_STEP_NODE = "run_step_node"
    CLEANUP = "cleanup"
    END = "end"


PIPELINE_TRANSITIONS = {
    AftersalesFlowState.START: AftersalesFlowState.VALIDATE_FLOW,
    AftersalesFlowState.VALIDATE_FLOW: AftersalesFlowState.RESOLVE_STEP,
    AftersalesFlowState.RESOLVE_STEP: AftersalesFlowState.RUN_STEP_NODE,
    AftersalesFlowState.RUN_STEP_NODE: AftersalesFlowState.CLEANUP,
    AftersalesFlowState.CLEANUP: AftersalesFlowState.END,
}

STEP_TO_NODE_KEY = {
    "select_order": "select_order",
    "select_type": "select_type",
    "select_reason": "select_reason",
    "input_description": "input_description",
    "confirm": "confirm",
    "submit": "submit",
    "result": "result",
    "cancel": "cancel",
}


def next_state(current: AftersalesFlowState) -> AftersalesFlowState:
    return PIPELINE_TRANSITIONS[current]
