"""Aftersales flow contracts."""
from __future__ import annotations

from typing import Any, Dict, TypedDict


class AftersalesFlowPayload(TypedDict, total=False):
    action: str
    step: str
    order_id: str
    order_no: str
    status: str
    refund_type: str
    reason: str
    description: str
    refund_amount: float
    extra: Dict[str, Any]
