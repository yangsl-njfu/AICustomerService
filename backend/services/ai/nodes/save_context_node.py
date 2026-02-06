"""
上下文保存节点
"""
from .base import BaseNode
from ..state import ConversationState
from services.redis_cache import redis_cache


class SaveContextNode(BaseNode):
    """上下文保存节点"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """保存上下文"""
        # 添加新的对话轮次到上下文
        await redis_cache.add_message_to_context(
            session_id=state["session_id"],
            user_message=state["user_message"],
            assistant_message=state["response"]
        )
        
        # 更新最后意图
        await redis_cache.update_context(
            session_id=state["session_id"],
            last_intent=state.get("intent")
        )
        
        return state
