"""Document response node."""
from __future__ import annotations

from ...state import ConversationState

from .base_step_node import DocumentAnalysisStepNode


class DocumentRespondNode(DocumentAnalysisStepNode):
    async def execute(self, state: ConversationState) -> ConversationState:
        return await self.service.generate_response(state)

    async def execute_stream(self, state: ConversationState):
        async for token in self.service.generate_response_stream(state):
            yield token
