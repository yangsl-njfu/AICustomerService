"""
AI workflow orchestrator.

The workflow stays generic. Business-specific tools, prompts, and model
selection are injected through AIRuntime instead of being hardcoded here.
"""
from __future__ import annotations

import logging
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from config import init_chat_model, init_intent_model

from .constants import INTENT_QA, INTENT_RECOMMEND
from .handler_registry import HandlerRegistry
from .nodes import (
    AftersalesFlowNode,
    ClarifyNode,
    ContextNode,
    DocumentNode,
    FunctionCallingNode,
    IntentRecognitionNode,
    OrderQueryNode,
    ProductInquiryNode,
    PurchaseFlowNode,
    PurchaseGuideNode,
    QANode,
    SaveContextNode,
    TicketNode,
    TopicAdvisorNode,
)
from .router import Router
from .runtime import runtime_factory
from .state import ConversationState

logger = logging.getLogger(__name__)


class AIWorkflow:
    """Generic workflow kernel for a single business runtime."""

    def __init__(self, runtime=None):
        self.runtime = runtime or runtime_factory.get_runtime()
        self.llm = self.runtime.get_chat_model("chat") if self.runtime else init_chat_model()
        self.intent_llm = self.runtime.get_chat_model("intent") if self.runtime else init_intent_model()
        self.router = Router(runtime=self.runtime)

        self.context_node = ContextNode()
        self.intent_node = IntentRecognitionNode(self.intent_llm, runtime=self.runtime)
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

    def _register_builtin_handlers(self):
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
        workflow.add_node("intent_recognition", self.intent_node.execute)
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
        workflow.add_edge("load_context", "intent_recognition")
        workflow.add_edge("intent_recognition", "function_calling")

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

    async def _safe_save_context(self, state: ConversationState):
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
        state = await self.intent_node.execute(state)
        logger.info(
            "intent_node completed in %.2fs intent=%s",
            time.time() - t0,
            state.get("intent"),
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

        if state.get("intent") == INTENT_RECOMMEND:
            logger.info("Recommendation intent routed directly to topic advisor agent")
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

        if state.get("intent") == INTENT_RECOMMEND:
            logger.info("Streaming recommendation via topic advisor agent")
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
    """Lazy compatibility proxy for legacy imports."""

    def __getattr__(self, item: str):
        return getattr(runtime_factory.get_workflow(), item)


ai_workflow = _DefaultWorkflowProxy()
