"""QA prepare node."""
from __future__ import annotations

from ...state import ConversationState

from .base_step_node import QAFlowStepNode


class QAPrepareNode(QAFlowStepNode):
    async def execute(self, state: ConversationState) -> ConversationState:
        await self.service.prepare_messages(state)
        return state
