"""会话控制回复节点。

当入口层已经判断“这轮不应该直接推进业务技能”时，
由这里统一生成：

- 侧话题的自然接话回复
- 主任务卡住时的帮助回复
- 取消任务后的收口回复
- 少量必要的澄清回复
"""
from __future__ import annotations

from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from .base import BaseNode
from ..constants import (
    RESPONSE_MODE_ANSWER_THEN_RESUME,
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
    """生成打断、接话、帮助、取消时的统一回复。"""

    def _build_reference_clarification(self, state: ConversationState, step_hint: Optional[str]) -> str:
        user_message = (state.get("user_message") or "").strip()
        quoted = f"“{user_message}”" if user_message else "这句话"

        if state.get("current_step") == "select_recommended_item":
            return (
                f"{quoted}里指的对象我还没对上。"
                "你可以直接说“第一个”“第二个”或者“那个 Python 的”，我就顺着接下去。"
            )

        if step_hint:
            return (
                f"{quoted}里指的内容还不够具体。"
                f"你把和“{step_hint}”相关的对象再说清一点，我就直接接着答。"
            )

        return (
            f"{quoted}里有个指代我还没完全对上。"
            "你把对象或想问的内容再说具体一点，我就直接接着回答。"
        )

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

    def _recent_history(self, state: ConversationState, limit: int = 3) -> str:
        history = state.get("conversation_history") or []
        if not history:
            return "(无)"

        lines = []
        for turn in history[-limit:]:
            lines.append(f"用户：{turn.get('user', '')}")
            lines.append(f"助手：{turn.get('assistant', '')}")
        return "\n".join(lines)

    async def _generate_side_topic_reply(self, state: ConversationState, flow_label: str, step_hint: Optional[str]) -> str:
        if self.llm is None:
            return (
                f"我先接住你这句。刚才的{flow_label}我还替你记着，"
                "后面你想继续时，直接顺着说就可以。"
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """你是一个自然、灵动的中文 AI 助手。

当前上下文里有一个尚未完成的主任务，但用户这一轮临时聊到了别的话题。
你的目标：
1. 先自然接住用户当前这句话，像正常聊天一样回复。
2. 不要逼用户做“继续还是切换”的二选一。
3. 可以很轻地带一句“刚才那个任务我还记着”，但不要重复追问。
4. 如果当前消息像闲聊、感叹、顺手提问，就优先自然接话。
5. 回复控制在 2 到 4 句，中文自然口语化。
6. 如果你对事实并不确定，就别编造得过于绝对。""",
                ),
                (
                    "human",
                    """当前主任务：{flow_label}
当前停留点：{step_hint}
最近对话：
{history}

用户这一轮说：{message}

请直接输出给用户的回复：""",
                ),
            ]
        )

        response = await self.llm.ainvoke(
            prompt.format_messages(
                flow_label=flow_label,
                step_hint=step_hint or "未显式记录",
                history=self._recent_history(state),
                message=state.get("user_message", ""),
            )
        )
        content = response.content if hasattr(response, "content") else str(response)
        return (content or "").strip()

    async def execute(self, state: ConversationState) -> ConversationState:
        response_mode = state.get("response_mode")
        flow_label = self._flow_label(state)
        step_hint = self._step_hint(state)

        if response_mode == RESPONSE_MODE_ANSWER_THEN_RESUME:
            state["response"] = await self._generate_side_topic_reply(state, flow_label, step_hint)
            state["quick_actions"] = None
            return state

        if response_mode == RESPONSE_MODE_CANCEL_CURRENT_TASK:
            state["response"] = (
                f"好的，我先把刚才的{flow_label}停在这里。"
                "后面如果还想接着办，直接说“继续刚才那个”就行。"
            )
            state["quick_actions"] = None
            return state

        if response_mode == RESPONSE_MODE_HELP_CURRENT_TASK:
            extra = f" 当前看起来更像是卡在“{step_hint}”这一步。" if step_hint else ""
            state["response"] = (
                f"我先不继续推进刚才的{flow_label}。{extra}"
                "你直接告诉我具体卡在哪、哪一步不会操作，"
                "我先把这一步讲清楚，再陪你往下走。"
            )
            state["quick_actions"] = None
            return state

        if response_mode == RESPONSE_MODE_CLARIFY_BEFORE_RESUME:
            state["response"] = self._build_reference_clarification(state, step_hint)
            state["quick_actions"] = None
            return state

        state["response"] = (
            f"我先把刚才的{flow_label}保留着。"
            "你想继续就顺着说，想聊新的内容我也能直接接住。"
        )
        state["quick_actions"] = None
        return state
