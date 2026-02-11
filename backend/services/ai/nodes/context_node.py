"""
上下文加载节点
"""
from datetime import datetime
from .base import BaseNode
from ..state import ConversationState
from services.redis_cache import redis_cache


class ContextNode(BaseNode):
    """上下文加载节点"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """加载会话上下文"""
        context = await redis_cache.get_context(state["session_id"])
        
        if context:
            state["conversation_history"] = context.get("history", [])
            state["user_profile"] = context.get("user_profile", {})
            state["intent_history"] = context.get("intent_history", [])
            state["conversation_summary"] = context.get("conversation_summary", "")
        else:
            state["conversation_history"] = []
            state["user_profile"] = {}
            state["intent_history"] = []
            state["conversation_summary"] = ""
        
        state["timestamp"] = datetime.now().isoformat()
        return state
