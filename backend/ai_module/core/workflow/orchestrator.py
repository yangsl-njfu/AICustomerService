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
from importlib import import_module
from typing import Any, Dict, Optional

from config import init_chat_model, init_intent_model

from ..constants import CONTROL_RESPONSE_MODES, INTENT_QA, INTENT_RECOMMEND
from .handler_registry import HandlerRegistry
from ..nodes import (
    ContextNode,
    ConversationControlNode,
    DialogueStateNode,
    FunctionCallingNode,
    MessageEntryNode,
    PolicyNode,
    ResponsePlannerNode,
    SaveContextNode,
)
from .router import Router
from ..runtime import runtime_factory
from ..state import ConversationState

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
        self.conversation_control_node = ConversationControlNode(self.llm, runtime=self.runtime)
        self.dialogue_state_node = DialogueStateNode()
        self.function_calling_node = FunctionCallingNode(self.llm, runtime=self.runtime)
        self.save_context_node = SaveContextNode(self.llm)
        self._lazy_nodes: Dict[str, Any] = {}

        self.handlers = HandlerRegistry()
        self._register_builtin_handlers()
        self.graph = None

    def _register_builtin_handlers(self) -> None:
        self.handlers.register("qa_flow", factory=self._get_qa_node, stream_enabled=True)
        self.handlers.register("ticket_flow", factory=self._get_ticket_node)
        self.handlers.register("document_analysis", factory=self._get_document_node, stream_enabled=True)
        self.handlers.register("clarify", factory=self._get_clarify_node, stream_enabled=True)
        self.handlers.register("product_inquiry", factory=self._get_product_inquiry_node)
        self.handlers.register("order_query", factory=self._get_order_query_node)
        self.handlers.register("purchase_guide", factory=self._get_purchase_guide_node, stream_enabled=True)
        self.handlers.register("aftersales_flow", factory=self._get_aftersales_flow_node)
        self.handlers.register("topic_advisor", factory=self._get_topic_advisor_node, stream_enabled=True)

    def _get_or_create_node(self, key: str, factory):
        node = self._lazy_nodes.get(key)
        if node is None:
            node = factory()
            self._lazy_nodes[key] = node
        return node

    def _instantiate_node(self, key: str, module_path: str, class_name: str, *args, **kwargs):
        return self._get_or_create_node(
            key,
            lambda: getattr(import_module(module_path), class_name)(*args, **kwargs),
        )

    def _get_qa_node(self):
        return self._instantiate_node(
            "qa_flow",
            "ai_module.core.nodes.qa_node",
            "QANode",
            self.llm,
            runtime=self.runtime,
        )

    def _get_document_node(self):
        return self._instantiate_node(
            "document_analysis",
            "ai_module.core.nodes.document_node",
            "DocumentNode",
            self.llm,
        )

    def _get_ticket_node(self):
        return self._instantiate_node(
            "ticket_flow",
            "ai_module.core.nodes.ticket_node",
            "TicketNode",
            self.llm,
        )

    def _get_clarify_node(self):
        return self._instantiate_node(
            "clarify",
            "ai_module.core.nodes.clarify_node",
            "ClarifyNode",
            self.llm,
        )

    def _get_product_inquiry_node(self):
        return self._instantiate_node(
            "product_inquiry",
            "ai_module.core.nodes.product_inquiry_node",
            "ProductInquiryNode",
            self.llm,
        )

    def _get_order_query_node(self):
        return self._instantiate_node(
            "order_query",
            "ai_module.core.nodes.order_query_node",
            "OrderQueryNode",
            self.llm,
        )

    def _get_purchase_guide_node(self):
        return self._instantiate_node(
            "purchase_guide",
            "ai_module.core.nodes.purchase_guide_node",
            "PurchaseGuideNode",
            self.llm,
        )

    def _get_purchase_flow_node(self):
        return self._instantiate_node(
            "purchase_flow",
            "ai_module.core.nodes.purchase_flow_node",
            "PurchaseFlowNode",
        )

    def _get_aftersales_flow_node(self):
        return self._instantiate_node(
            "aftersales_flow",
            "ai_module.core.nodes.aftersales_flow_node",
            "AftersalesFlowNode",
        )

    def _get_topic_advisor_node(self):
        return self._instantiate_node(
            "topic_advisor",
            "ai_module.core.nodes.topic_advisor_node",
            "TopicAdvisorNode",
            self.llm,
            runtime=self.runtime,
        )

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

    async def _load_context_only(
        self,
        user_id: str,
        session_id: str,
        message: str,
        attachments=None,
        purchase_flow=None,
        aftersales_flow=None,
    ) -> ConversationState:
        state = self._make_initial_state(
            user_id=user_id,
            session_id=session_id,
            message=message,
            attachments=attachments,
            purchase_flow=purchase_flow,
            aftersales_flow=aftersales_flow,
        )
        return await self.context_node.execute(state)

    async def _run_prepare_pipeline(self, state: ConversationState) -> ConversationState:
        logger.info("Preparing intent for session=%s", state.get("session_id"))
        total_start = time.time()

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

        if self._should_clarify(state):
            logger.info("prepare_intent completed in %.2fs via clarify", time.time() - total_start)
            return state

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
        if purchase_flow or aftersales_flow:
            final_state = await self._load_context_only(
                user_id=user_id,
                session_id=session_id,
                message=message,
                attachments=attachments,
                purchase_flow=purchase_flow,
                aftersales_flow=aftersales_flow,
            )
            final_state = await self.generate_response(final_state)
        else:
            prepared_state = await self.prepare_intent(
                user_id=user_id,
                session_id=session_id,
                message=message,
                attachments=attachments,
            )
            final_state = await self.generate_response(prepared_state)

        final_state["processing_time"] = (datetime.now() - start_time).total_seconds()
        return final_state

    async def prepare_intent(
        self,
        user_id,
        session_id,
        message,
        attachments=None,
        purchase_flow=None,
        aftersales_flow=None,
    ):
        state = self._make_initial_state(
            user_id=user_id,
            session_id=session_id,
            message=message,
            attachments=attachments,
            purchase_flow=purchase_flow,
            aftersales_flow=aftersales_flow,
        )
        return await self._run_prepare_pipeline(state)

    async def generate_response(self, state):
        purchase_flow = state.get("purchase_flow")
        if purchase_flow:
            logger.info("Purchase flow detected step=%s", purchase_flow.get("step"))
            try:
                result_state = await self._get_purchase_flow_node().execute(state)
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
                result_state = await self._get_aftersales_flow_node().execute(state)
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
            result_state = await self._get_clarify_node().execute(state)
            state.update(result_state)
            return state

        if state.get("intent") == INTENT_RECOMMEND:
            logger.info("Recommendation intent routed directly to topic advisor")
            try:
                result_state = await self._get_topic_advisor_node().execute(state)
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
        node = self.handlers.get(route, default=self._get_qa_node())

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
                result_state = await self._get_purchase_flow_node().execute(state)
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
                result_state = await self._get_aftersales_flow_node().execute(state)
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
            result_state = await self._get_clarify_node().execute(state)
            state.update(result_state)
            if state.get("response"):
                yield {"type": "content", "delta": state["response"]}
            yield {"type": "end", "quick_actions": state.get("quick_actions")}
            return

        if state.get("intent") == INTENT_RECOMMEND:
            logger.info("Streaming recommendation via topic advisor")
            try:
                async for token in self._get_topic_advisor_node().execute_stream(state):
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
            node = self.handlers.get(route, default=self._get_qa_node())
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

        if purchase_flow or aftersales_flow:
            state = await self._load_context_only(
                user_id=user_id,
                session_id=session_id,
                message=message,
                attachments=attachments,
                purchase_flow=purchase_flow,
                aftersales_flow=aftersales_flow,
            )
            intent = (
                state.get("intent")
                or (state.get("active_task") or {}).get("intent")
                or state.get("last_intent")
                or INTENT_QA
            )
        else:
            state = await self.prepare_intent(user_id, session_id, message, attachments)
            intent = state.get("intent", INTENT_QA)

        yield {"type": "intent", "intent": intent}

        async for event in self.generate_response_stream(state):
            if event.get("type") == "end":
                event["processing_time"] = (datetime.now() - start_time).total_seconds()
            yield event


class _DefaultWorkflowProxy:
    """兼容旧导入路径的惰性代理。"""

    def __getattr__(self, item: str):
        return getattr(runtime_factory.get_workflow(), item)


ai_workflow = _DefaultWorkflowProxy()
