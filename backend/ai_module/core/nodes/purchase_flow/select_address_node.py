"""Purchase select address step node."""
from __future__ import annotations

from ai_module.core.state import ConversationState

from .base_step_node import PurchaseFlowStepNode


class PurchaseSelectAddressNode(PurchaseFlowStepNode):
    async def execute(self, state: ConversationState) -> ConversationState:
        return await self.service.handle_select_address(state, self._get_flow_data(state))
