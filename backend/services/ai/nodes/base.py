"""
AI 工作流节点基类。
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..state import ConversationState


class BaseNode(ABC):
    """工作流抽象节点。"""

    def __init__(self, llm=None, runtime=None):
        self.llm = llm
        self.runtime = runtime

    @abstractmethod
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行当前节点逻辑。"""

    def validate_state(self, state: ConversationState) -> bool:
        return True

    async def on_error(self, state: ConversationState, error: Exception) -> ConversationState:
        state["response"] = f"抱歉，处理您的请求时出现了问题: {error}"
        return state
