"""
Base node primitives for AI workflows.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..state import ConversationState


class BaseNode(ABC):
    """Abstract workflow node."""

    def __init__(self, llm=None, runtime=None):
        self.llm = llm
        self.runtime = runtime

    @abstractmethod
    async def execute(self, state: ConversationState) -> ConversationState:
        """Execute node logic."""

    def validate_state(self, state: ConversationState) -> bool:
        return True

    async def on_error(self, state: ConversationState, error: Exception) -> ConversationState:
        state["response"] = f"抱歉，处理您的请求时出现了问题: {error}"
        return state
