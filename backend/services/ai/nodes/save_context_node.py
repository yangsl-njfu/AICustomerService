"""
上下文保存节点。

需求：
- 3.1：对话历史超过阈值时触发摘要
- 3.2：摘要压缩早期历史并保留关键信息
- 3.3：摘要后保留最近对话原文
- 3.6：摘要失败时回退到截断策略
- 3.7：将摘要与对话历史持久化到缓存服务
"""
import copy
import logging
from .base import BaseNode
from ..constants import (
    RESPONSE_MODE_CANCEL_CURRENT_TASK,
    RESPONSE_MODE_CLARIFY_BEFORE_RESUME,
    RESPONSE_MODE_HELP_CURRENT_TASK,
)
from ..state import ConversationState
from ..summarizer import ConversationSummarizer
from services.redis_cache import redis_cache

logger = logging.getLogger(__name__)


class SaveContextNode(BaseNode):
    """在业务节点结束后保存下一轮所需的上下文。

    在骨架设计里，这个节点承担“闭环持久化层”的职责：
    当前轮的响应会在这里转化为下一轮的起始上下文。
    """

    def __init__(self, llm=None):
        super().__init__(llm)
        self.summarizer = ConversationSummarizer(llm) if llm else None

    def _response_requires_follow_up(self, response: str) -> bool:
        normalized = (response or "").strip()
        if not normalized:
            return False
        if normalized.endswith(("?", "？")):
            return True
        return any(
            token in normalized
            for token in ("请问", "请选择", "是否", "要不要", "需要我", "可以为您", "需要您", "下一步")
        )

    def _infer_pending_action(self, state: ConversationState) -> str | None:
        if state.get("purchase_flow"):
            return "purchase_flow_step"
        if state.get("aftersales_flow"):
            return "aftersales_flow_step"

        quick_actions = state.get("quick_actions") or []
        if quick_actions:
            action_types = {action.get("type") for action in quick_actions}
            action_names = {action.get("action") for action in quick_actions}

            if "product" in action_types:
                return "select_recommended_item"
            if "order_card" in action_types or "order_card_simple" in action_types or "open_order_selector" in action_names:
                return "select_order"
            if "coupon" in action_types:
                return "select_coupon"
            if "address" in action_types:
                return "select_address"
            return "choose_next_step"

        if self._response_requires_follow_up(state.get("response", "")):
            return "answer_follow_up"

        return None

    def _update_task_state(self, state: ConversationState) -> None:
        active_task = copy.deepcopy(state.get("active_task"))
        response_mode = state.get("response_mode")

        if response_mode == RESPONSE_MODE_CANCEL_CURRENT_TASK:
            state["active_task"] = None
            state["pending_question"] = None
            state["pending_action"] = None
            return

        if not active_task:
            state["pending_question"] = None
            state["pending_action"] = None
            return

        # 推断助手下一步在等什么，便于下一轮用户输入按未完成任务来解释。
        pending_action = self._infer_pending_action(state)
        pending_question = state.get("response", "").strip() if pending_action else None

        if response_mode in {
            RESPONSE_MODE_CLARIFY_BEFORE_RESUME,
            RESPONSE_MODE_HELP_CURRENT_TASK,
        }:
            resume_pending_action = (
                active_task.get("resume_pending_action")
                or active_task.get("pending_action")
                or state.get("pending_action")
            )
            resume_pending_question = (
                active_task.get("resume_pending_question")
                or active_task.get("pending_question")
                or state.get("pending_question")
            )

            active_task["resume_mode"] = state.get("resume_mode")
            active_task["resume_pending_action"] = resume_pending_action
            active_task["resume_pending_question"] = resume_pending_question
            active_task["last_response"] = state.get("response", "")
            active_task["last_quick_actions"] = copy.deepcopy(state.get("quick_actions") or [])
            active_task["status"] = "awaiting_user"
            active_task["updated_at"] = state.get("timestamp")

            state["active_task"] = active_task
            state["pending_question"] = resume_pending_question
            state["pending_action"] = resume_pending_action
            return

        active_task["pending_action"] = pending_action
        active_task["pending_question"] = pending_question
        active_task["last_response"] = state.get("response", "")
        active_task["last_quick_actions"] = copy.deepcopy(state.get("quick_actions") or [])
        active_task["status"] = "awaiting_user" if pending_action else "completed"
        active_task["updated_at"] = state.get("timestamp")

        state["active_task"] = active_task
        state["pending_question"] = pending_question
        state["pending_action"] = pending_action

    async def execute(self, state: ConversationState) -> ConversationState:
        """保存当前轮上下文。"""
        self._update_task_state(state)

        # 先把当前轮对话写入会话历史。
        await redis_cache.add_message_to_context(
            session_id=state["session_id"],
            user_message=state["user_message"],
            assistant_message=state["response"]
        )

        # 同时持久化传统历史字段和多轮对话状态字段。
        await redis_cache.update_context(
            session_id=state["session_id"],
            last_intent=state.get("intent") or (state.get("active_task") or {}).get("intent") or state.get("last_intent"),
            intent_history=state.get("intent_history", []),
            last_quick_actions=state.get("quick_actions") or [],
            active_task=state.get("active_task"),
            task_stack=state.get("task_stack") or [],
            pending_question=state.get("pending_question"),
            pending_action=state.get("pending_action"),
        )

        # 对话变长时，按需触发摘要压缩。
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
