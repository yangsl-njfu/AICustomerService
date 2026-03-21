"""Base class for order query workflow nodes."""
from __future__ import annotations

from ..common.base import BaseNode
from ...workflows.order_query.service import OrderQueryService


class OrderQueryStepNode(BaseNode):
    """Shared helper for order query workflow nodes."""

    def __init__(self, service: OrderQueryService):
        super().__init__()
        self.service = service
