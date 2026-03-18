"""会话控制规划节点。

这个节点不负责识别用户想表达什么，而是把入口分类结果转成系统接下来
应该采用的回复模式与恢复策略：
- 继续当前任务
- 先处理阻塞，再回到当前任务
- 先澄清当前是在继续还是切换
- 结束当前任务
- 切换到新任务
"""
from __future__ import annotations

from .base import BaseNode
from ..constants import (
    INFLOW_CANCEL_FLOW,
    INFLOW_CORRECTION,
    INFLOW_HANDOFF,
    INFLOW_IRRELEVANT,
    INFLOW_RELATED_BLOCKER,
    INFLOW_RELATED_QUESTION,
    INFLOW_SWITCH_FLOW,
    INFLOW_UNKNOWN,
    INFLOW_VALID_CURRENT_INPUT,
    RESUME_MODE_RESTART_FLOW,
    RESUME_MODE_RESUME_EXACT,
    RESUME_MODE_RESUME_FROM_SAFE_STEP,
    RESPONSE_MODE_CANCEL_CURRENT_TASK,
    RESPONSE_MODE_CLARIFY_BEFORE_RESUME,
    RESPONSE_MODE_CONTINUE_CURRENT_TASK,
    RESPONSE_MODE_HANDOFF,
    RESPONSE_MODE_HELP_CURRENT_TASK,
    RESPONSE_MODE_SWITCH_TASK,
)
from ..state import ConversationState


class ResponsePlannerNode(BaseNode):
    """根据流程内分类结果选择回复模式与恢复策略。"""

    async def execute(self, state: ConversationState) -> ConversationState:
        state["response_mode"] = RESPONSE_MODE_CONTINUE_CURRENT_TASK
        state["resume_mode"] = None

        if not state.get("has_active_flow"):
            return state

        inflow_type = state.get("inflow_type")

        if inflow_type in {INFLOW_VALID_CURRENT_INPUT, INFLOW_CORRECTION, INFLOW_RELATED_QUESTION}:
            state["response_mode"] = RESPONSE_MODE_CONTINUE_CURRENT_TASK
            state["resume_mode"] = RESUME_MODE_RESUME_EXACT
            return state

        if inflow_type == INFLOW_RELATED_BLOCKER:
            state["response_mode"] = RESPONSE_MODE_HELP_CURRENT_TASK
            state["resume_mode"] = RESUME_MODE_RESUME_FROM_SAFE_STEP
            state["continue_previous_task"] = False
            state["need_clarification"] = False
            return state

        if inflow_type == INFLOW_IRRELEVANT:
            state["response_mode"] = RESPONSE_MODE_CLARIFY_BEFORE_RESUME
            state["resume_mode"] = RESUME_MODE_RESUME_EXACT
            state["continue_previous_task"] = False
            state["need_clarification"] = False
            return state

        if inflow_type == INFLOW_UNKNOWN:
            state["response_mode"] = RESPONSE_MODE_CLARIFY_BEFORE_RESUME
            state["resume_mode"] = RESUME_MODE_RESUME_FROM_SAFE_STEP
            state["continue_previous_task"] = False
            state["need_clarification"] = False
            return state

        if inflow_type == INFLOW_CANCEL_FLOW:
            state["response_mode"] = RESPONSE_MODE_CANCEL_CURRENT_TASK
            state["resume_mode"] = None
            state["continue_previous_task"] = False
            state["need_clarification"] = False
            return state

        if inflow_type == INFLOW_HANDOFF:
            state["response_mode"] = RESPONSE_MODE_HANDOFF
            state["resume_mode"] = None
            state["continue_previous_task"] = False
            return state

        if inflow_type == INFLOW_SWITCH_FLOW:
            state["response_mode"] = RESPONSE_MODE_SWITCH_TASK
            state["resume_mode"] = RESUME_MODE_RESTART_FLOW
            state["continue_previous_task"] = False
            return state

        return state
