"""
上下文保存节点

Requirements:
- 3.1: 对话历史超过阈值时触发摘要
- 3.2: 摘要压缩早期历史，保留关键信息
- 3.3: 摘要后保留最近对话原文
- 3.6: 摘要失败时回退截断
- 3.7: 摘要与对话历史持久化到 Redis Cache
"""
import logging
from .base import BaseNode
from ..state import ConversationState
from ..summarizer import ConversationSummarizer
from services.redis_cache import redis_cache

logger = logging.getLogger(__name__)


class SaveContextNode(BaseNode):
    """上下文保存节点"""

    def __init__(self, llm=None):
        super().__init__(llm)
        self.summarizer = ConversationSummarizer(llm) if llm else None

    async def execute(self, state: ConversationState) -> ConversationState:
        """保存上下文"""
        # 添加新的对话轮次到上下文
        await redis_cache.add_message_to_context(
            session_id=state["session_id"],
            user_message=state["user_message"],
            assistant_message=state["response"]
        )

        # 更新最后意图和意图历史
        await redis_cache.update_context(
            session_id=state["session_id"],
            last_intent=state.get("intent"),
            intent_history=state.get("intent_history", [])
        )

        # 检查是否需要摘要
        if self.summarizer:
            context = await redis_cache.get_context(state["session_id"])
            history = context.get("history", [])
            if self.summarizer.should_summarize(history):
                try:
                    result = await self.summarizer.summarize(
                        history,
                        context.get("conversation_summary", "")
                    )
                    await redis_cache.update_context(
                        session_id=state["session_id"],
                        history=result["remaining_history"],
                        conversation_summary=result["summary"]
                    )
                except Exception:
                    logger.warning(
                        "摘要生成失败，执行回退截断",
                        exc_info=True
                    )
                    truncated = self.summarizer.fallback_truncate(history)
                    await redis_cache.update_context(
                        session_id=state["session_id"],
                        history=truncated["remaining_history"]
                    )

        return state
