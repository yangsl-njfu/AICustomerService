"""Base class for purchase flow step nodes."""
from __future__ import annotations

from ..common.base import BaseNode
from ...state import ConversationState
from ...workflows.purchase_flow.service import PurchaseFlowService


class PurchaseFlowStepNode(BaseNode):
    """Shared helper for purchase flow step nodes."""

    def __init__(self, service: PurchaseFlowService | None = None):
        super().__init__()
        self.service = service or PurchaseFlowService()

    def _get_flow_data(self, state: ConversationState) -> dict:
        return state.get("purchase_flow") or {}
