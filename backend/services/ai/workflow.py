"""
AI 工作流编排器。

当前版本优先保证主链路稳定：
1. 先加载上下文
2. 再做消息入口分类
3. 根据入口分类规划回复模式
4. 进入意图决策与状态更新
5. 调用工具并路由到具体业务技能
6. 保存上下文，供下一轮继续使用

这里保留了原有业务技能节点，只收口会话主干，避免入口层与业务层耦合。
"""
from __future__ import annotations

import logging
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from config import init_chat_model, init_intent_model

from .constants import CONTROL_RESPONSE_MODES, INTENT_QA, INTENT_RECOMMEND
from .handler_registry import HandlerRegistry
from .nodes import (
    AftersalesFlowNode,
    ClarifyNode,
    ContextNode,
    ConversationControlNode,
    DialogueStateNode,
    DocumentNode,
    FunctionCallingNode,
    MessageEntryNode,
    OrderQueryNode,
    PolicyNode,
    ProductInquiryNode,
    PurchaseFlowNode,
    PurchaseGuideNode,
    QANode,
    ResponsePlannerNode,
    SaveContextNode,
    TicketNode,
    TopicAdvisorNode,
)
from .router import Router
from .runtime import runtime_factory
from .state import ConversationState

logger = logging.getLogger(__name__)


class AIWorkflow:
    """单业务运行时下的 AI 工作流。"""

    def __init__(self, runtime=None):
        self.runtime = runtime or runtime_factory.get_runtime()
        self.llm = self.runtime.get_chat_model("chat") if self.runtime else init_chat_model()
        self.intent_llm = self.runtime.get_chat_model("intent") if self.runtime else init_intent_model()
        self.router = Router(runtime=self.runtime)

        self.context_node = ContextNode()
        self.message_entry_node = MessageEntryNode(self.intent_llm, runtime=self.runtime)
        self.response_planner_node = ResponsePlannerNode(runtime=self.runtime)
        self.policy_node = PolicyNode(runtime=self.runtime)
        self.conversation_control_node = ConversationControlNode(self.llm)
        self.dialogue_state_node = DialogueStateNode()
        self.function_calling_node = FunctionCallingNode(self.llm, runtime=self.runtime)
        self.save_context_node = SaveContextNode(self.llm)

        self.qa_node = QANode(self.llm)
        self.document_node = DocumentNode(self.llm)
        self.ticket_node = TicketNode(self.llm)
        self.clarify_node = ClarifyNode(self.llm)
        self.product_inquiry_node = ProductInquiryNode(self.llm)
        self.order_query_node = OrderQueryNode(self.llm)
        self.purchase_guide_node = PurchaseGuideNode(self.llm)
        self.purchase_flow_node = PurchaseFlowNode()
        self.aftersales_flow_node = AftersalesFlowNode()
        self.topic_advisor_node = TopicAdvisorNode(self.llm, runtime=self.runtime)

        self.handlers = HandlerRegistry()
        self._register_builtin_handlers()
        self.graph = self._build_graph()

    def _register_builtin_handlers(self) -> None:
        self.handlers.register("qa_flow", self.qa_node, stream_enabled=True)
        self.handlers.register("ticket_flow", self.ticket_node)
        self.handlers.register("document_analysis", self.document_node, stream_enabled=True)
        self.handlers.register("clarify", self.clarify_node, stream_enabled=True)
        self.handlers.register("product_inquiry", self.product_inquiry_node)
        self.handlers.register("order_query", self.order_query_node)
        self.handlers.register("purchase_guide", self.purchase_guide_node, stream_enabled=True)
        self.handlers.register("aftersales_flow", self.aftersales_flow_node)
        self.handlers.register("topic_advisor", self.topic_advisor_node, stream_enabled=True)

    def _build_graph(self):
        workflow = StateGraph(ConversationState)

        workflow.add_node("load_context", self.context_node.execute)
        workflow.add_node("message_entry", self.message_entry_node.execute)
        workflow.add_node("response_planner", self.response_planner_node.execute)
        workflow.add_node("conversation_control", self.conversation_control_node.execute)
        workflow.add_node("policy", self.policy_node.execute)
        workflow.add_node("dialogue_state", self.dialogue_state_node.execute)
        workflow.add_node("function_calling", self.function_calling_node.execute)
        workflow.add_node("save_context", self.save_context_node.execute)

        workflow.add_node("qa_flow", self.qa_node.execute)
        workflow.add_node("document_analysis", self.document_node.execute)
        workflow.add_node("ticket_flow", self.ticket_node.execute)
        workflow.add_node("clarify", self.clarify_node.execute)
        workflow.add_node("product_inquiry", self.product_inquiry_node.execute)
        workflow.add_node("order_query", self.order_query_node.execute)
        workflow.add_node("purchase_guide", self.purchase_guide_node.execute)
        workflow.add_node("topic_advisor", self.topic_advisor_node.execute)
        workflow.add_node("aftersales_flow", self.aftersales_flow_node.execute)

        workflow.set_entry_point("load_context")
        workflow.add_edge("load_context", "message_entry")
        workflow.add_edge("message_entry", "response_planner")
        workflow.add_conditional_edges(
            "response_planner",
            self._route_after_response_planner,
            {
                "conversation_control": "conversation_control",
                "policy": "policy",
            },
        )
        workflow.add_conditional_edges(
            "policy",
            self._route_after_understanding,
            {
                "dialogue_state": "dialogue_state",
                "clarify": "clarify",
            },
        )
        workflow.add_edge("dialogue_state", "function_calling")
        workflow.add_conditional_edges(
            "function_calling",
            self.router.route_after_function_calling,
            {
                "qa_flow": "qa_flow",
                "ticket_flow": "ticket_flow",
                "document_analysis": "document_analysis",
                "product_inquiry": "product_inquiry",
                "purchase_guide": "purchase_guide",
                "order_query": "order_query",
                "topic_advisor": "topic_advisor",
                "aftersales_flow": "aftersales_flow",
                "clarify": "clarify",
            },
        )

        workflow.add_edge("conversation_control", "save_context")
        workflow.add_edge("qa_flow", "save_context")
        workflow.add_edge("ticket_flow", "save_context")
        workflow.add_edge("document_analysis", "save_context")
        workflow.add_edge("product_inquiry", "save_context")
        workflow.add_edge("purchase_guide", "save_context")
        workflow.add_edge("order_query", "save_context")
        workflow.add_edge("topic_advisor", "save_context")
        workflow.add_edge("aftersales_flow", "save_context")

        workflow.add_edge("clarify", END)
        workflow.add_edge("save_context", END)
        return workflow.compile()

    def _route_after_response_planner(self, state: ConversationState) -> str:
        if self._should_use_conversation_control(state):
            return "conversation_control"
        return "policy"

    def _route_after_understanding(self, state: ConversationState) -> str:
        if self._should_clarify(state):
            return "clarify"
        return "dialogue_state"

    def _should_use_conversation_control(self, state: ConversationState) -> bool:
        return state.get("response_mode") in CONTROL_RESPONSE_MODES

    def _should_clarify(self, state: ConversationState) -> bool:
        if self._should_use_conversation_control(state):
            return False
        if state.get("need_clarification"):
            return True
        confidence = float(state.get("confidence") or 0.0)
        return not state.get("intent") and confidence < 0.6

    def _make_initial_state(
        self,
        user_id: str,
        session_id: str,
        message: str,
        attachments: Optional[list] = None,
        purchase_flow: Optional[Dict[str, Any]] = None,
        aftersales_flow: Optional[Dict[str, Any]] = None,
    ) -> ConversationState:
        execution_context = None
        business_id = None
        if self.runtime is not None:
            business_id = self.runtime.business_pack.business_id
            execution_context = asdict(
                self.runtime.build_context(
                    user_id=user_id,
                    session_id=session_id,
                    extra={"attachments": attachments or []},
                )
            )

        return {
            "user_message": message,
            "user_id": user_id,
            "session_id": session_id,
            "business_id": business_id,
            "execution_context": execution_context,
            "attachments": attachments or [],
            "conversation_history": [],
            "user_profile": {},
            "last_intent": None,
            "last_quick_actions": [],
            "active_task": None,
            "task_stack": [],
            "pending_question": None,
            "pending_action": None,
            "entry_classifier": None,
            "has_active_flow": False,
            "active_flow": None,
            "current_step": None,
            "expected_user_acts": [],
            "expected_slot": None,
            "expected_input_type": None,
            "semantic_source": None,
            "intent_hint": None,
            "semantic_confidence": None,
            "policy_action": None,
            "skill_route": None,
            "inflow_type": None,
            "flow_relation": None,
            "response_mode": None,
            "resume_mode": None,
            "dialogue_act": None,
            "domain_intent": None,
            "self_contained_request": False,
            "continue_previous_task": False,
            "need_clarification": False,
            "understanding_confidence": None,
            "slot_updates": {},
            "reference_resolution": None,
            "selected_quick_action": None,
            "intent": None,
            "confidence": None,
            "retrieved_docs": None,
            "tool_result": None,
            "tool_used": None,
            "response": "",
            "sources": None,
            "ticket_id": None,
            "recommended_products": None,
            "quick_actions": None,
            "timestamp": "",
            "processing_time": None,
            "intent_history": [],
            "conversation_summary": "",
            "purchase_flow": purchase_flow,
            "aftersales_flow": aftersales_flow,
            "topic_advisor_projects": [],
            "topic_advisor_tool_results": [],
        }

    async def _safe_save_context(self, state: ConversationState) -> None:
        try:
            await self.save_context_node.execute(state)
        except Exception:
            logger.warning("Failed to persist conversation context", exc_info=True)

    async def process_message(
        self,
        user_id: str,
        session_id: str,
        message: str,
        attachments=None,
        purchase_flow=None,
        aftersales_flow=None,
    ):
        start_time = datetime.now()
        initial_state = self._make_initial_state(
            user_id=user_id,
            session_id=session_id,
            message=message,
            attachments=attachments,
            purchase_flow=purchase_flow,
            aftersales_flow=aftersales_flow,
        )

        if purchase_flow or aftersales_flow:
            final_state = await self.generate_response(initial_state)
        else:
            final_state = await self.graph.ainvoke(initial_state)

        final_state["processing_time"] = (datetime.now() - start_time).total_seconds()
        return final_state

    async def prepare_intent(self, user_id, session_id, message, attachments=None):
        logger.info("Preparing intent for session=%s", session_id)
        total_start = time.time()
        state = self._make_initial_state(user_id, session_id, message, attachments)

        t0 = time.time()
        state = await self.context_node.execute(state)
        logger.info("context_node completed in %.2fs", time.time() - t0)

        t0 = time.time()
        state = await self.message_entry_node.execute(state)
        logger.info(
            "message_entry_node completed in %.2fs entry_classifier=%s inflow_type=%s intent=%s active_flow=%s current_step=%s",
            time.time() - t0,
            state.get("entry_classifier"),
            state.get("inflow_type"),
            state.get("intent"),
            state.get("active_flow"),
            state.get("current_step"),
        )

        t0 = time.time()
        state = await self.response_planner_node.execute(state)
        logger.info(
            "response_planner_node completed in %.2fs response_mode=%s resume_mode=%s",
            time.time() - t0,
            state.get("response_mode"),
            state.get("resume_mode"),
        )

        if self._should_use_conversation_control(state):
            logger.info("prepare_intent completed in %.2fs via conversation_control", time.time() - total_start)
            return state

        t0 = time.time()
        state = await self.policy_node.execute(state)
        logger.info(
            "policy_node completed in %.2fs intent=%s confidence=%s need_clarification=%s",
            time.time() - t0,
            state.get("intent"),
            state.get("confidence"),
            state.get("need_clarification"),
        )

        t0 = time.time()
        state = await self.dialogue_state_node.execute(state)
        logger.info(
            "dialogue_state_node completed in %.2fs active_task=%s stack_size=%s",
            time.time() - t0,
            (state.get("active_task") or {}).get("intent"),
            len(state.get("task_stack") or []),
        )

        logger.info("prepare_intent completed in %.2fs", time.time() - total_start)
        return state

    async def generate_response(self, state):
        purchase_flow = state.get("purchase_flow")
        if purchase_flow:
            logger.info("Purchase flow detected step=%s", purchase_flow.get("step"))
            try:
                result_state = await self.purchase_flow_node.execute(state)
                state.update(result_state)
                await self._safe_save_context(state)
                return state
            except Exception as exc:
                logger.error("Purchase flow failed: %s", exc, exc_info=True)
                state["response"] = "抱歉，购买流程出现了问题，请重新开始。"
                return state

        aftersales_flow = state.get("aftersales_flow")
        if aftersales_flow:
            logger.info("Aftersales flow detected step=%s", aftersales_flow.get("step"))
            try:
                result_state = await self.aftersales_flow_node.execute(state)
                state.update(result_state)
                await self._safe_save_context(state)
                return state
            except Exception as exc:
                logger.error("Aftersales flow failed: %s", exc, exc_info=True)
                state["response"] = "抱歉，售后流程出现了问题，请重新开始。"
                return state

        logger.info("Generating response intent=%s", state.get("intent"))

        if self._should_use_conversation_control(state):
            result_state = await self.conversation_control_node.execute(state)
            state.update(result_state)
            await self._safe_save_context(state)
            return state

        if self._should_clarify(state):
            result_state = await self.clarify_node.execute(state)
            state.update(result_state)
            return state

        if state.get("intent") == INTENT_RECOMMEND:
            logger.info("Recommendation intent routed directly to topic advisor")
            try:
                result_state = await self.topic_advisor_node.execute(state)
                state.update(result_state)
            except Exception as exc:
                logger.error("Topic advisor failed: %s", exc, exc_info=True)
                state["response"] = "抱歉，处理您的请求时出现了问题，请稍后再试。"
            await self._safe_save_context(state)
            return state

        t0 = time.time()
        state = await self.function_calling_node.execute(state)
        logger.info(
            "function_calling_node completed in %.2fs tool_used=%s",
            time.time() - t0,
            state.get("tool_used"),
        )

        route = self.router.route_after_function_calling(state)
        node = self.handlers.get(route, default=self.qa_node)

        try:
            result_state = await node.execute(state)
            state.update(result_state)
        except Exception as exc:
            logger.error("Node %s failed: %s", route, exc, exc_info=True)
            state["response"] = "抱歉，处理您的请求时出现了问题，请稍后再试。"

        if route != "clarify":
            await self._safe_save_context(state)

        return state

    async def generate_response_stream(self, state):
        purchase_flow = state.get("purchase_flow")
        if purchase_flow:
            logger.info("Streaming purchase flow step=%s", purchase_flow.get("step"))
            try:
                result_state = await self.purchase_flow_node.execute(state)
                state.update(result_state)
                await self._safe_save_context(state)
                yield {"type": "content", "delta": state.get("response", "")}
                yield {"type": "end", "status": "success", "quick_actions": state.get("quick_actions")}
                return
            except Exception as exc:
                logger.error("Purchase flow streaming failed: %s", exc, exc_info=True)
                yield {"type": "content", "delta": "抱歉，购买流程出现了问题，请重新开始。"}
                yield {"type": "end", "status": "error"}
                return

        aftersales_flow = state.get("aftersales_flow")
        if aftersales_flow:
            logger.info("Streaming aftersales flow step=%s", aftersales_flow.get("step"))
            try:
                result_state = await self.aftersales_flow_node.execute(state)
                state.update(result_state)
                await self._safe_save_context(state)
                yield {"type": "content", "delta": state.get("response", "")}
                yield {"type": "end", "status": "success", "quick_actions": state.get("quick_actions")}
                return
            except Exception as exc:
                logger.error("Aftersales flow streaming failed: %s", exc, exc_info=True)
                yield {"type": "content", "delta": "抱歉，售后流程出现了问题，请重新开始。"}
                yield {"type": "end", "status": "error"}
                return

        if self._should_use_conversation_control(state):
            result_state = await self.conversation_control_node.execute(state)
            state.update(result_state)
            if state.get("response"):
                yield {"type": "content", "delta": state["response"]}
            await self._safe_save_context(state)
            yield {"type": "end", "quick_actions": state.get("quick_actions")}
            return

        if self._should_clarify(state):
            result_state = await self.clarify_node.execute(state)
            state.update(result_state)
            if state.get("response"):
                yield {"type": "content", "delta": state["response"]}
            yield {"type": "end", "quick_actions": state.get("quick_actions")}
            return

        if state.get("intent") == INTENT_RECOMMEND:
            logger.info("Streaming recommendation via topic advisor")
            try:
                async for token in self.topic_advisor_node.execute_stream(state):
                    yield {"type": "content", "delta": token}
            except Exception as exc:
                logger.error("Topic advisor streaming failed: %s", exc, exc_info=True)
                yield {"type": "content", "delta": "抱歉，处理您的请求时出现了问题，请稍后再试。"}
            await self._safe_save_context(state)
            yield {
                "type": "end",
                "quick_actions": state.get("quick_actions"),
                "recommended_products": state.get("recommended_products"),
            }
            return

        t0 = time.time()
        state = await self.function_calling_node.execute(state)
        logger.info("function_calling_node completed in %.2fs", time.time() - t0)

        route = self.router.route_after_function_calling(state)
        logger.info("stream route=%s", route)

        stream_node = self.handlers.get_stream(route)
        if stream_node is not None:
            try:
                async for token in stream_node.execute_stream(state):
                    yield {"type": "content", "delta": token}
            except Exception as exc:
                logger.error("Streaming node %s failed: %s", route, exc, exc_info=True)
                state["response"] = "抱歉，处理您的请求时出现了问题，请稍后再试。"
                yield {"type": "content", "delta": state["response"]}
        else:
            node = self.handlers.get(route, default=self.qa_node)
            try:
                result_state = await node.execute(state)
                state.update(result_state)
            except Exception as exc:
                logger.error("Node %s failed: %s", route, exc, exc_info=True)
                state["response"] = "抱歉，处理您的请求时出现了问题，请稍后再试。"
            if state.get("response"):
                yield {"type": "content", "delta": state["response"]}

        if route != "clarify":
            await self._safe_save_context(state)

        yield {
            "type": "end",
            "sources": state.get("sources"),
            "quick_actions": state.get("quick_actions"),
            "recommended_products": state.get("recommended_products"),
        }

    async def process_message_stream(
        self,
        user_id,
        session_id,
        message,
        attachments=None,
        purchase_flow=None,
        aftersales_flow=None,
    ):
        start_time = datetime.now()

        state = await self.prepare_intent(user_id, session_id, message, attachments)
        if purchase_flow:
            state["purchase_flow"] = purchase_flow
        if aftersales_flow:
            state["aftersales_flow"] = aftersales_flow

        yield {"type": "intent", "intent": state.get("intent", INTENT_QA)}

        async for event in self.generate_response_stream(state):
            if event.get("type") == "end":
                event["processing_time"] = (datetime.now() - start_time).total_seconds()
            yield event


class _DefaultWorkflowProxy:
    """兼容旧导入路径的惰性代理。"""

    def __getattr__(self, item: str):
        return getattr(runtime_factory.get_workflow(), item)


ai_workflow = _DefaultWorkflowProxy()
