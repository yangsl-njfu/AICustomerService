"""会话控制回复节点。

当入口已经判断出当前消息不应该直接落到业务技能节点时，由这个节点统一生成：
- 跑题后的拉回回复
- 卡住时的帮助回复
- 取消当前任务后的收口回复
"""
from __future__ import annotations

from typing import Optional

from .base import BaseNode
from ..constants import (
    RESUME_MODE_RESUME_FROM_SAFE_STEP,
    RESPONSE_MODE_CANCEL_CURRENT_TASK,
    RESPONSE_MODE_CLARIFY_BEFORE_RESUME,
    RESPONSE_MODE_HELP_CURRENT_TASK,
)
from ..state import ConversationState

_FLOW_LABELS = {
    "purchase_flow": "购买流程",
    "aftersales_flow": "售后流程",
}

_STEP_HINTS = {
    "select_recommended_item": "刚才那批推荐里更偏向哪一个",
    "select_order": "您要处理的是哪一个订单",
    "select_coupon": "想使用哪一张优惠券",
    "select_address": "收货地址该怎么选",
    "answer_follow_up": "上一个问题还差哪部分信息",
    "choose_next_step": "下一步想继续哪种操作",
}


class ConversationControlNode(BaseNode):
    """生成打断、拉回与取消时的统一回复。"""

    def _flow_label(self, state: ConversationState) -> str:
        active_flow = state.get("active_flow")
        if active_flow in _FLOW_LABELS:
            return _FLOW_LABELS[active_flow]
        if active_flow:
            return f"{active_flow}任务"
        return "当前任务"

    def _step_hint(self, state: ConversationState) -> Optional[str]:
        current_step = state.get("current_step")
        if current_step in _STEP_HINTS:
            return _STEP_HINTS[current_step]
        pending_question = (state.get("pending_question") or "").strip()
        if pending_question:
            return pending_question
        return None

    async def execute(self, state: ConversationState) -> ConversationState:
        response_mode = state.get("response_mode")
        flow_label = self._flow_label(state)
        step_hint = self._step_hint(state)
        resume_mode = state.get("resume_mode")

        if response_mode == RESPONSE_MODE_CANCEL_CURRENT_TASK:
            state["response"] = (
                f"好的，我先把刚才的{flow_label}停在这里。"
                "如果之后还想接着办，直接说“继续刚才那个”就可以。"
            )
            state["quick_actions"] = None
            return state

        if response_mode == RESPONSE_MODE_HELP_CURRENT_TASK:
            extra = ""
            if step_hint:
                extra = f" 当前更像是卡在“{step_hint}”这一步。"
            state["response"] = (
                f"我先不继续推进刚才的{flow_label}。{extra}"
                "您可以直接告诉我具体卡在哪一步、哪里不会操作，我先把这一步说明清楚，再继续往下走。"
            )
            state["quick_actions"] = None
            return state

        if response_mode == RESPONSE_MODE_CLARIFY_BEFORE_RESUME:
            if resume_mode == RESUME_MODE_RESUME_FROM_SAFE_STEP:
                suffix = "如果您想继续，我会从最近一个安全步骤接上，不会直接把流程重来。"
            else:
                suffix = "如果您想继续，我会直接接回刚才停住的位置。"

            hint_text = f" 当前我们停在“{step_hint}”。" if step_hint else ""
            state["response"] = (
                f"我先确认一下，您这句话和当前正在进行的{flow_label}没有直接接上。"
                f"{hint_text}您是想继续刚才的{flow_label}，还是准备切换到新的问题？{suffix}"
            )
            state["quick_actions"] = None
            return state

        state["response"] = (
            f"我先把刚才的{flow_label}保留着。"
            "如果您想继续，直接告诉我下一步要补什么信息；如果想切换话题，也可以直接说新的需求。"
        )
        state["quick_actions"] = None
        return state
