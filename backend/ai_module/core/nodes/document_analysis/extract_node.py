"""Document extraction node."""
from __future__ import annotations

from ...state import ConversationState

from .base_step_node import DocumentAnalysisStepNode


class DocumentExtractNode(DocumentAnalysisStepNode):
    async def execute(self, state: ConversationState) -> ConversationState:
        await self.service.prepare_attachments(state)
        return state
