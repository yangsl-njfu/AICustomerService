"""统一会话入口节点。

这个节点是对话层唯一的前门。

- 当不存在活动流程时，它负责做全局任务识别，回答：
  “用户现在想开启什么新业务任务？”
- 当已经存在活动流程时，它负责做流程内输入识别，回答：
  “这句话相对于当前流程起什么作用？”

工作流其他部分不需要再猜该走哪条识别路径，
这一层会把入口分流决策统一收口。
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate

from .base import BaseNode
from .intent_node import IntentRecognitionNode
from .turn_understanding_node import TurnUnderstandingNode
from ..constants import (
    DIALOGUE_ACT_NEW_REQUEST,
    DIALOGUE_ACT_REJECT,
    DIALOGUE_ACT_SWITCH_TOPIC,
    DIALOGUE_ACT_UNCLEAR,
    ENTRY_CLASSIFIER_GLOBAL,
    ENTRY_CLASSIFIER_INFLOW,
    INFLOW_CANCEL_FLOW,
    INFLOW_CORRECTION,
    INFLOW_HANDOFF,
    INFLOW_IRRELEVANT,
    INFLOW_RELATED_BLOCKER,
    INFLOW_RELATED_QUESTION,
    INFLOW_SWITCH_FLOW,
    INFLOW_TYPES,
    INFLOW_UNKNOWN,
    INFLOW_VALID_CURRENT_INPUT,
    INTENT_TICKET,
)
from ..state import ConversationState

logger = logging.getLogger(__name__)

_HANDOFF_RE = re.compile(r"(转人工|人工客服|客服介入|我要投诉|投诉|升级处理|找客服)", re.IGNORECASE)
_CANCEL_RE = re.compile(r"^(取消|不办了|先不弄了|先这样吧|算了|不用了|结束流程|退出流程)$", re.IGNORECASE)
_BLOCKER_RE = re.compile(r"(不会|不懂|不知道怎么|找不到|没找到|没有这个|上传不了|打不开|进不去|操作不了)", re.IGNORECASE)
_SMALLTALK_RE = re.compile(r"^(你好|hello|hi|在吗|谢谢|辛苦了|哈哈|好的谢谢|没事了)$", re.IGNORECASE)


class MessageEntryNode(BaseNode):
    """根据会话状态选择正确识别器的统一入口节点。"""

    def __init__(self, llm=None, runtime=None):
        super().__init__(llm=llm, runtime=runtime)
        self.global_intent_classifier = IntentRecognitionNode(llm=llm, runtime=runtime)
        self.inflow_understanding = TurnUnderstandingNode(llm=llm, runtime=runtime)

    def _reset_entry_fields(self, state: ConversationState) -> None:
        state["entry_classifier"] = None
        state["has_active_flow"] = False
        state["active_flow"] = None
        state["current_step"] = None
        state["expected_user_acts"] = []
        state["inflow_type"] = None
        state["flow_relation"] = None
        state["response_mode"] = None
        state["resume_mode"] = None
        state["dialogue_act"] = None
        state["domain_intent"] = None
        state["self_contained_request"] = False
        state["continue_previous_task"] = False
        state["need_clarification"] = False
        state["understanding_confidence"] = None
        state["slot_updates"] = {}
        state["reference_resolution"] = None
        state["selected_quick_action"] = None
        state["intent"] = None
        state["confidence"] = None

    def _has_active_flow(self, state: ConversationState) -> bool:
        if state.get("purchase_flow") or state.get("aftersales_flow"):
            return True

        active_task = state.get("active_task") or {}
        if active_task.get("status") in {"active", "awaiting_user"}:
            return True

        return bool(state.get("pending_action") or state.get("pending_question"))

    def _resolve_active_flow(self, state: ConversationState) -> tuple[Optional[str], Optional[str]]:
        if state.get("purchase_flow"):
            flow = state["purchase_flow"] or {}
            return "purchase_flow", flow.get("step")

        if state.get("aftersales_flow"):
            flow = state["aftersales_flow"] or {}
            return "aftersales_flow", flow.get("step")

        active_task = state.get("active_task") or {}
        active_flow = active_task.get("intent") or state.get("last_intent")
        current_step = active_task.get("pending_action") or state.get("pending_action")
        return active_flow, current_step

    def _derive_expected_user_acts(self, state: ConversationState, current_step: Optional[str]) -> List[str]:
        if current_step == "select_recommended_item":
            return [
                INFLOW_VALID_CURRENT_INPUT,
                INFLOW_CORRECTION,
                INFLOW_RELATED_QUESTION,
                INFLOW_SWITCH_FLOW,
                INFLOW_CANCEL_FLOW,
            ]
        if current_step in {"select_order", "select_coupon", "select_address"}:
            return [
                INFLOW_VALID_CURRENT_INPUT,
                INFLOW_RELATED_QUESTION,
                INFLOW_RELATED_BLOCKER,
                INFLOW_SWITCH_FLOW,
                INFLOW_CANCEL_FLOW,
            ]
        if current_step in {"purchase_flow_step", "aftersales_flow_step"}:
            return [
                INFLOW_VALID_CURRENT_INPUT,
                INFLOW_RELATED_QUESTION,
                INFLOW_RELATED_BLOCKER,
                INFLOW_CORRECTION,
                INFLOW_SWITCH_FLOW,
                INFLOW_CANCEL_FLOW,
                INFLOW_HANDOFF,
            ]
        if current_step in {"answer_follow_up", "choose_next_step"}:
            return [
                INFLOW_VALID_CURRENT_INPUT,
                INFLOW_RELATED_QUESTION,
                INFLOW_RELATED_BLOCKER,
                INFLOW_SWITCH_FLOW,
                INFLOW_CANCEL_FLOW,
                INFLOW_HANDOFF,
                INFLOW_IRRELEVANT,
            ]

        if self._has_active_flow(state):
            return [
                INFLOW_VALID_CURRENT_INPUT,
                INFLOW_RELATED_QUESTION,
                INFLOW_RELATED_BLOCKER,
                INFLOW_CORRECTION,
                INFLOW_SWITCH_FLOW,
                INFLOW_CANCEL_FLOW,
                INFLOW_HANDOFF,
                INFLOW_IRRELEVANT,
                INFLOW_UNKNOWN,
            ]
        return []

    def _append_preselected_intent(self, state: ConversationState, intent: Optional[str], confidence: float) -> None:
        if not intent:
            return
        intent_history = state.get("intent_history") or []
        self.global_intent_classifier._append_intent_history(state, intent_history, intent, confidence)

    def _format_recent_history(self, history: List[Dict[str, Any]], limit: int = 3) -> str:
        if not history:
            return "(none)"
        lines: List[str] = []
        for turn in history[-limit:]:
            lines.append(f"user: {turn.get('user', '')}")
            lines.append(f"assistant: {turn.get('assistant', '')}")
        return "\n".join(lines)

    def _extract_json_block(self, text: str) -> Optional[str]:
        if not text:
            return None
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced:
            return fenced.group(1)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return text[start : end + 1]

    def _normalize_inflow_llm_result(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        inflow_type = payload.get("inflow_type")
        if inflow_type not in INFLOW_TYPES:
            return None

        confidence = payload.get("confidence")
        try:
            confidence = max(0.0, min(1.0, float(confidence)))
        except (TypeError, ValueError):
            confidence = None

        return {
            "inflow_type": inflow_type,
            "domain_intent": payload.get("domain_intent"),
            "continue_previous_task": bool(payload.get("continue_previous_task", False)),
            "need_clarification": bool(payload.get("need_clarification", False)),
            "confidence": confidence,
        }

    def _build_inflow_prompt(self) -> ChatPromptTemplate:
        system_prompt = """你负责识别“已有活动流程中的用户输入”。
只输出 JSON，不要输出解释。

输出字段：
- inflow_type: 必须是 valid_current_input/related_question/related_blocker/correction/switch_flow/cancel_flow/handoff/irrelevant/unknown 之一
- domain_intent: 业务意图标签，无法确定时输出 null
- continue_previous_task: 布尔值
- need_clarification: 布尔值
- confidence: 0 到 1 之间的数字

判断原则：
1. 只有当消息可以被当前流程直接消费时，才使用 valid_current_input。
2. 只有当用户明确开启不同业务任务时，才使用 switch_flow。
3. irrelevant 用于不会替换当前任务的闲聊或顺带提问。
4. 如果消息过于模糊，无法安全执行，就使用 unknown。
5. 除非切换任务非常明确，否则 domain_intent 保持为 null。
"""
        return ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", "{input_payload}")]
        )

    async def _infer_inflow_with_llm(
        self,
        state: ConversationState,
        *,
        active_flow: Optional[str],
        current_step: Optional[str],
        expected_user_acts: List[str],
        rule_guess: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        if self.llm is None:
            return None

        prompt = self._build_inflow_prompt()
        payload = {
            "message": state.get("user_message"),
            "active_flow": active_flow,
            "current_step": current_step,
            "pending_action": state.get("pending_action"),
            "pending_question": state.get("pending_question"),
            "expected_user_acts": expected_user_acts,
            "rule_guess": rule_guess,
            "recent_history": self._format_recent_history(state.get("conversation_history") or []),
        }
        try:
            response = await self.llm.ainvoke(
                prompt.format_messages(
                    input_payload=json.dumps(payload, ensure_ascii=False, indent=2)
                )
            )
            raw = response.content if hasattr(response, "content") else str(response)
            json_block = self._extract_json_block(raw)
            if not json_block:
                return None
            parsed = json.loads(json_block)
            if not isinstance(parsed, dict):
                return None
            return self._normalize_inflow_llm_result(parsed)
        except Exception as exc:
            logger.warning("Message entry inflow LLM fallback failed: %s", exc)
            return None

    async def _run_global_intent(self, state: ConversationState) -> ConversationState:
        state["entry_classifier"] = ENTRY_CLASSIFIER_GLOBAL
        state["flow_relation"] = "no_flow"
        state["dialogue_act"] = DIALOGUE_ACT_NEW_REQUEST
        state["self_contained_request"] = True
        state["continue_previous_task"] = False

        result = await self.global_intent_classifier.execute(state)
        if result.get("intent"):
            confidence = float(result.get("confidence") or 0.9)
            result["domain_intent"] = result.get("intent")
            result["understanding_confidence"] = confidence
            result["need_clarification"] = False
        else:
            result["need_clarification"] = True
            result["understanding_confidence"] = float(result.get("confidence") or 0.3)
        return result

    def _is_switch_request(self, state: ConversationState, active_flow: Optional[str]) -> bool:
        hinted_intent = state.get("domain_intent")
        if not state.get("self_contained_request"):
            return False
        if not hinted_intent:
            return False
        return hinted_intent != active_flow

    def _apply_non_switch_inflow(self, state: ConversationState, active_flow: Optional[str], inflow_type: str) -> ConversationState:
        state["inflow_type"] = inflow_type
        state["self_contained_request"] = False
        state["continue_previous_task"] = inflow_type in {
            INFLOW_VALID_CURRENT_INPUT,
            INFLOW_CORRECTION,
            INFLOW_RELATED_QUESTION,
        }

        if inflow_type in {INFLOW_VALID_CURRENT_INPUT, INFLOW_CORRECTION, INFLOW_RELATED_QUESTION}:
            state["flow_relation"] = "continue"
        elif inflow_type == INFLOW_RELATED_BLOCKER:
            state["flow_relation"] = "pause"
        elif inflow_type == INFLOW_CANCEL_FLOW:
            state["flow_relation"] = "cancel"
        elif inflow_type == INFLOW_IRRELEVANT:
            state["flow_relation"] = "interrupt"
        else:
            state["flow_relation"] = "clarify"

        if inflow_type == INFLOW_UNKNOWN:
            state["need_clarification"] = True
            state["dialogue_act"] = DIALOGUE_ACT_UNCLEAR
            state["confidence"] = float(state.get("understanding_confidence") or 0.3)
            return state

        if active_flow and inflow_type in {
            INFLOW_VALID_CURRENT_INPUT,
            INFLOW_CORRECTION,
            INFLOW_RELATED_QUESTION,
            INFLOW_RELATED_BLOCKER,
        }:
            confidence = float(state.get("confidence") or state.get("understanding_confidence") or 0.88)
            state["intent"] = active_flow
            state["confidence"] = confidence
            self._append_preselected_intent(state, active_flow, confidence)
        return state

    async def _run_inflow_classifier(self, state: ConversationState) -> ConversationState:
        active_flow = state.get("active_flow")
        current_step = state.get("current_step")
        expected_user_acts = state.get("expected_user_acts") or []
        message = (state.get("user_message") or "").strip()

        state["entry_classifier"] = ENTRY_CLASSIFIER_INFLOW

        if _HANDOFF_RE.search(message):
            state["inflow_type"] = INFLOW_HANDOFF
            state["flow_relation"] = "handoff"
            state["dialogue_act"] = DIALOGUE_ACT_SWITCH_TOPIC
            state["self_contained_request"] = True
            state["continue_previous_task"] = False
            state["intent"] = INTENT_TICKET
            state["domain_intent"] = INTENT_TICKET
            state["understanding_confidence"] = 0.96
            state["confidence"] = 0.96
            self._append_preselected_intent(state, INTENT_TICKET, 0.96)
            return state

        if _CANCEL_RE.match(message):
            state["inflow_type"] = INFLOW_CANCEL_FLOW
            state["flow_relation"] = "cancel"
            state["dialogue_act"] = DIALOGUE_ACT_REJECT
            state["self_contained_request"] = False
            state["continue_previous_task"] = True
            state["understanding_confidence"] = 0.95
            return self._apply_non_switch_inflow(state, active_flow, INFLOW_CANCEL_FLOW)

        state = await self.inflow_understanding.execute(state)

        if self._is_switch_request(state, active_flow):
            state["inflow_type"] = INFLOW_SWITCH_FLOW
            state["flow_relation"] = "switch"
            state["dialogue_act"] = DIALOGUE_ACT_NEW_REQUEST
            state["continue_previous_task"] = False
            state["self_contained_request"] = True
            switched = await self.global_intent_classifier.execute(state)
            switched["entry_classifier"] = ENTRY_CLASSIFIER_INFLOW
            switched["has_active_flow"] = True
            switched["active_flow"] = active_flow
            switched["current_step"] = current_step
            switched["expected_user_acts"] = expected_user_acts
            switched["inflow_type"] = INFLOW_SWITCH_FLOW
            switched["flow_relation"] = "switch"
            if not switched.get("intent") and state.get("domain_intent"):
                switched["intent"] = state["domain_intent"]
                switched["confidence"] = max(float(state.get("understanding_confidence") or 0.0), 0.85)
                self._append_preselected_intent(
                    switched,
                    switched["intent"],
                    float(switched["confidence"]),
                )
            switched["domain_intent"] = switched.get("intent") or state.get("domain_intent")
            switched["understanding_confidence"] = float(
                switched.get("confidence") or state.get("understanding_confidence") or 0.85
            )
            switched["need_clarification"] = not bool(switched.get("intent"))
            return switched

        if state.get("continue_previous_task"):
            inflow_type = INFLOW_CORRECTION if state.get("dialogue_act") == "correct" else INFLOW_VALID_CURRENT_INPUT
            return self._apply_non_switch_inflow(state, active_flow, inflow_type)

        if (
            state.get("self_contained_request")
            and state.get("domain_intent") == active_flow
            and active_flow
            and state.get("slot_updates")
        ):
            inflow_type = INFLOW_CORRECTION if state.get("slot_updates") else INFLOW_RELATED_QUESTION
            state["continue_previous_task"] = True
            return self._apply_non_switch_inflow(state, active_flow, inflow_type)

        llm_result = await self._infer_inflow_with_llm(
            state,
            active_flow=active_flow,
            current_step=current_step,
            expected_user_acts=expected_user_acts,
            rule_guess=None,
        )
        if llm_result:
            inflow_type = llm_result["inflow_type"]
            state["inflow_type"] = inflow_type
            state["domain_intent"] = state.get("domain_intent") or llm_result.get("domain_intent")
            state["need_clarification"] = llm_result["need_clarification"]
            if llm_result.get("confidence") is not None:
                state["understanding_confidence"] = llm_result["confidence"]
            if inflow_type == INFLOW_SWITCH_FLOW:
                state["self_contained_request"] = True
                state["continue_previous_task"] = False
                state["dialogue_act"] = DIALOGUE_ACT_NEW_REQUEST
                state["flow_relation"] = "switch"
                switched = await self.global_intent_classifier.execute(state)
                switched["entry_classifier"] = ENTRY_CLASSIFIER_INFLOW
                switched["has_active_flow"] = True
                switched["active_flow"] = active_flow
                switched["current_step"] = current_step
                switched["expected_user_acts"] = expected_user_acts
                switched["inflow_type"] = INFLOW_SWITCH_FLOW
                switched["flow_relation"] = "switch"
                switched["domain_intent"] = switched.get("intent") or state.get("domain_intent")
                switched["understanding_confidence"] = float(
                    switched.get("confidence") or state.get("understanding_confidence") or 0.85
                )
                switched["need_clarification"] = not bool(switched.get("intent"))
                return switched
            if inflow_type == INFLOW_HANDOFF:
                state["intent"] = INTENT_TICKET
                state["domain_intent"] = INTENT_TICKET
                state["confidence"] = max(float(state.get("understanding_confidence") or 0.0), 0.9)
                self._append_preselected_intent(state, INTENT_TICKET, float(state["confidence"]))
                state["flow_relation"] = "handoff"
                return state
            return self._apply_non_switch_inflow(state, active_flow, inflow_type)

        if _BLOCKER_RE.search(message):
            return self._apply_non_switch_inflow(state, active_flow, INFLOW_RELATED_BLOCKER)
        if message.endswith(("?", "？")):
            return self._apply_non_switch_inflow(state, active_flow, INFLOW_RELATED_QUESTION)
        if _SMALLTALK_RE.match(message):
            return self._apply_non_switch_inflow(state, active_flow, INFLOW_IRRELEVANT)

        state["understanding_confidence"] = float(state.get("understanding_confidence") or 0.3)
        return self._apply_non_switch_inflow(state, active_flow, INFLOW_UNKNOWN)

    async def execute(self, state: ConversationState) -> ConversationState:
        self._reset_entry_fields(state)

        has_active_flow = self._has_active_flow(state)
        active_flow, current_step = self._resolve_active_flow(state)
        expected_user_acts = self._derive_expected_user_acts(state, current_step)

        state["has_active_flow"] = has_active_flow
        state["active_flow"] = active_flow
        state["current_step"] = current_step
        state["expected_user_acts"] = expected_user_acts

        if not has_active_flow:
            return await self._run_global_intent(state)

        return await self._run_inflow_classifier(state)
