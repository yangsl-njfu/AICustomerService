"""Purchase flow contracts."""
from __future__ import annotations

from typing import Any, Dict, TypedDict


class PurchaseFlowPayload(TypedDict, total=False):
    action: str
    step: str
    product_id: str
    coupon_id: str
    address_id: str
    order_id: str
    order_no: str
    final_price: float
    extra: Dict[str, Any]
