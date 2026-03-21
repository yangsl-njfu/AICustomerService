"""Topic advisor execution node."""
from __future__ import annotations

from typing import AsyncIterator

from ...state import ConversationState

from .base_step_node import TopicAdvisorStepNode


class TopicAdvisorExecuteNode(TopicAdvisorStepNode):
    async def execute(self, state: ConversationState) -> ConversationState:
        return await self.service.run_agent(state)

    async def execute_stream(self, state: ConversationState) -> AsyncIterator[str]:
        async for token in self.service.run_agent_stream(state):
            yield token
