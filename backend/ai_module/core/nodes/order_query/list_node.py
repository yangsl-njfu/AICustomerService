"""Order query list node."""
from __future__ import annotations

from ...state import ConversationState

from .base_step_node import OrderQueryStepNode


class OrderQueryListNode(OrderQueryStepNode):
    async def execute(self, state: ConversationState) -> ConversationState:
        return await self.service.handle_list_orders(state)
