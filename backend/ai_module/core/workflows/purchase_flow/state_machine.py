"""State machine for purchase flow workflow."""
from __future__ import annotations

from enum import Enum


class PurchaseFlowState(str, Enum):
    START = "start"
    VALIDATE_FLOW = "validate_flow"
    RESOLVE_STEP = "resolve_step"
    RUN_STEP_NODE = "run_step_node"
    CLEANUP = "cleanup"
    END = "end"


PIPELINE_TRANSITIONS = {
    PurchaseFlowState.START: PurchaseFlowState.VALIDATE_FLOW,
    PurchaseFlowState.VALIDATE_FLOW: PurchaseFlowState.RESOLVE_STEP,
    PurchaseFlowState.RESOLVE_STEP: PurchaseFlowState.RUN_STEP_NODE,
    PurchaseFlowState.RUN_STEP_NODE: PurchaseFlowState.CLEANUP,
    PurchaseFlowState.CLEANUP: PurchaseFlowState.END,
}

STEP_TO_NODE_KEY = {
    "confirm_product": "confirm_product",
    "select_coupon": "select_coupon",
    "confirm_coupon": "confirm_coupon",
    "select_address": "select_address",
    "confirm_address": "confirm_address",
    "order_confirm": "order_confirm",
    "payment": "payment",
    "payment_done": "payment_done",
    "payment_success": "payment_success",
}


def next_state(current: PurchaseFlowState) -> PurchaseFlowState:
    return PIPELINE_TRANSITIONS[current]
