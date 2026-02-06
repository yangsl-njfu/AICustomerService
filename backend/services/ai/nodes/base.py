"""
基础节点类
"""
from abc import ABC, abstractmethod
from ..state import ConversationState


class BaseNode(ABC):
    """基础节点抽象类"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    @abstractmethod
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行节点逻辑"""
        pass
    
    def validate_state(self, state: ConversationState) -> bool:
        """验证状态"""
        return True
    
    async def on_error(self, state: ConversationState, error: Exception) -> ConversationState:
        """错误处理"""
        state["response"] = f"抱歉，处理您的请求时出现了问题: {str(error)}"
        return state
