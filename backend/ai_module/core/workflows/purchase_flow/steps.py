"""Composable node helpers for purchase flow workflow."""
from __future__ import annotations

from typing import Dict

from ...nodes.common.base import BaseNode
from ...nodes.purchase_flow import (
    PurchaseConfirmAddressNode,
    PurchaseConfirmCouponNode,
    PurchaseConfirmProductNode,
    PurchaseOrderConfirmNode,
    PurchasePaymentDoneNode,
    PurchasePaymentNode,
    PurchasePaymentSuccessNode,
    PurchaseSelectAddressNode,
    PurchaseSelectCouponNode,
)
from ...state import ConversationState
from .service import PurchaseFlowService


def build_step_nodes(service: PurchaseFlowService | None = None) -> Dict[str, BaseNode]:
    shared_service = service or PurchaseFlowService()
    return {
        "confirm_product": PurchaseConfirmProductNode(shared_service),
        "select_coupon": PurchaseSelectCouponNode(shared_service),
        "confirm_coupon": PurchaseConfirmCouponNode(shared_service),
        "select_address": PurchaseSelectAddressNode(shared_service),
        "confirm_address": PurchaseConfirmAddressNode(shared_service),
        "order_confirm": PurchaseOrderConfirmNode(shared_service),
        "payment": PurchasePaymentNode(shared_service),
        "payment_done": PurchasePaymentDoneNode(shared_service),
        "payment_success": PurchasePaymentSuccessNode(shared_service),
    }


def cleanup_runtime_keys(state: ConversationState) -> ConversationState:
    state.pop("_purchase_flow_step", None)
    state.pop("_purchase_flow_node_key", None)
    return state
