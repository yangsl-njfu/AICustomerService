"""Workflow package base interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from ..state import ConversationState


class BaseWorkflow(ABC):
    """Base contract for pluggable business workflows."""

    name: str = "workflow"
    stream_enabled: bool = False

    @abstractmethod
    async def execute(self, state: ConversationState) -> ConversationState:
        """Execute a full workflow turn and return updated conversation state."""

    async def execute_stream(self, state: ConversationState) -> AsyncIterator[str]:
        """Stream workflow output token-by-token when supported."""
        result = await self.execute(state)
        for char in result.get("response", ""):
            yield char
