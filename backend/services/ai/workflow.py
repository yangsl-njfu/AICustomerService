"""
AI工作流编排器
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from config import settings, init_chat_model, init_intent_model

from .state import ConversationState
from .router import Router
from .nodes import (
    ContextNode,
    IntentRecognitionNode,
    FunctionCallingNode,
    SaveContextNode,
    QANode,
    DocumentNode,
    TicketNode,
    ClarifyNode,
    ProductInquiryNode,
    OrderQueryNode,
    PurchaseGuideNode,
    PurchaseFlowNode,
    AftersalesFlowNode,
    TopicAdvisorNode
)

logger = logging.getLogger(__name__)


class AIWorkflow:
    """AI工作流编排器"""
    
    def __init__(self):
        self.llm = init_chat_model()
        self.intent_llm = init_intent_model()
        self.router = Router()
        
        self.context_node = ContextNode()
        self.intent_node = IntentRecognitionNode(self.intent_llm)
        self.function_calling_node = FunctionCallingNode(self.llm)
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
        self.topic_advisor_node = TopicAdvisorNode(self.llm)
        
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """构建工作流图"""
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

        workflow.set_entry_point("load_context")
        workflow.add_edge("load_context", "intent_recognition")
        workflow.add_edge("intent_recognition", "function_calling")
        
        workflow.add_conditional_edges(
            "function_calling",
            self.router.route_after_function_calling,
            {
                "qa_flow": "qa_flow",
                "ticket_flow": "ticket_flow",
                "product_flow": "qa_flow",
                "document_analysis": "document_analysis",
                "product_inquiry": "product_inquiry",
                "purchase_guide": "purchase_guide",
                "order_query": "order_query",
                "topic_advisor": "topic_advisor",
                "clarify": "clarify"
            }
        )
        
        workflow.add_edge("qa_flow", "save_context")
        workflow.add_edge("ticket_flow", "save_context")
        workflow.add_edge("document_analysis", "save_context")
        workflow.add_edge("product_inquiry", "save_context")
        workflow.add_edge("purchase_guide", "save_context")
        workflow.add_edge("order_query", "save_context")
        workflow.add_edge("topic_advisor", "save_context")
        workflow.add_edge("clarify", END)
        workflow.add_edge("save_context", END)
        
        return workflow.compile()
    
    def _make_initial_state(self, user_id, session_id, message, attachments, purchase_flow=None, aftersales_flow=None):
        return ConversationState(
            user_message=message, user_id=user_id, session_id=session_id,
            attachments=attachments, conversation_history=[], user_profile={},
            intent=None, confidence=None, retrieved_docs=None,
            tool_result=None, tool_used=None, response="",
            sources=None, ticket_id=None, recommended_products=None,
            quick_actions=None, timestamp="", processing_time=None,
            intent_history=[], conversation_summary="",
            purchase_flow=purchase_flow, aftersales_flow=aftersales_flow,
            topic_advisor_projects=[], topic_advisor_tool_results=[]
        )

    async def process_message(self, user_id, session_id, message, attachments=None, purchase_flow=None):
        """处理用户消息（非流式）"""
        start_time = datetime.now()
        initial_state = self._make_initial_state(user_id, session_id, message, attachments, purchase_flow)
        final_state = await self.graph.ainvoke(initial_state)
        final_state["processing_time"] = (datetime.now() - start_time).total_seconds()
        return final_state
    
    # 支持流式输出的节点
    _STREAM_NODES = {"qa_flow", "document_analysis", "purchase_guide", "clarify"}
    # 不调用 LLM 的节点
    _NO_LLM_RESPONSE_NODES = {"product_recommendation", "product_inquiry", "order_query"}
    _PRE_RESPONSE_NODES = {"intent_recognition", "function_calling", "load_context", "save_context"}

    async def prepare_intent(self, user_id, session_id, message, attachments=None):
        """阶段1: 前置处理 + 意图识别，返回 state"""
        print(f"🔔 [prepare_intent] 开始处理: user_id={user_id}, message={message[:20]}...", flush=True)
        total_start = time.time()
        state = self._make_initial_state(user_id, session_id, message, attachments)

        t0 = time.time()
        state = await self.context_node.execute(state)
        logger.info(f"⏱️ [context_node] {time.time() - t0:.2f}s")

        t0 = time.time()
        state = await self.intent_node.execute(state)
        logger.info(f"⏱️ [intent_node] {time.time() - t0:.2f}s  → intent={state.get('intent')}")

        logger.info(f"⏱️ [prepare_intent 总计] {time.time() - total_start:.2f}s")
        return state

    async def generate_response(self, state):
        """阶段2: function calling + 路由 + 生成回答，返回 state"""
        
        purchase_flow = state.get("purchase_flow")
        if purchase_flow:
            logger.info(f"🛒 [generate_response] 检测到购买流程, step={purchase_flow.get('step')}")
            try:
                result_state = await self.purchase_flow_node.execute(state)
                state.update(result_state)
                return state
            except Exception as e:
                logger.error(f"购买流程执行失败: {e}")
                state["response"] = "抱歉，购买流程出现了问题，请重新开始。"
                return state

        aftersales_flow = state.get("aftersales_flow")
        if aftersales_flow:
            logger.info(f"🔄 [generate_response] 检测到售后流程, step={aftersales_flow.get('step')}")
            try:
                result_state = await self.aftersales_flow_node.execute(state)
                state.update(result_state)
                return state
            except Exception as e:
                logger.error(f"售后流程执行失败: {e}")
                state["response"] = "抱歉，售后流程出现了问题，请重新开始。"
                return state
        
        logger.info(f"🎯 [generate_response] 开始, intent={state.get('intent')}")

        # Agent 节点：跳过 function_calling，直接进入 Agent 自己的工具调用循环
        if state.get("intent") == "推荐":
            logger.info("🤖 [generate_response] 走 Agent 路径，跳过 function_calling")
            try:
                result_state = await self.topic_advisor_node.execute(state)
                state.update(result_state)
            except Exception as e:
                logger.error(f"Agent 执行失败: {e}")
                state["response"] = "抱歉，处理您的请求时出现了问题，请稍后再试。"
            try:
                await self.save_context_node.execute(state)
            except Exception:
                pass
            return state

        t0 = time.time()
        state = await self.function_calling_node.execute(state)
        logger.info(f"⏱️ [function_calling_node] {time.time() - t0:.2f}s, tool_used={state.get('tool_used')}")
        route = self.router.route_after_function_calling(state)
        
        node_map = {
            "product_inquiry": self.product_inquiry_node,
            "order_query": self.order_query_node,
            "clarify": self.clarify_node,
            "qa_flow": self.qa_node,
            "ticket_flow": self.ticket_node,
            "document_analysis": self.document_node,
            "purchase_guide": self.purchase_guide_node,
            "aftersales_flow": self.aftersales_flow_node,
            "topic_advisor": self.topic_advisor_node,
        }
        node = node_map.get(route, self.qa_node)
        
        try:
            result_state = await node.execute(state)
            state.update(result_state)
        except Exception as e:
            logger.error(f"节点执行失败: {e}")
            state["response"] = "抱歉，处理您的请求时出现了问题，请稍后再试。"
        
        if route != "clarify":
            try:
                await self.save_context_node.execute(state)
            except Exception:
                pass
        
        return state

    async def generate_response_stream(self, state):
        """阶段2 流式版: function calling + 路由 + 逐 token yield 回答"""
        
        purchase_flow = state.get("purchase_flow")
        if purchase_flow:
            logger.info(f"🛒 [generate_response_stream] 检测到购买流程, step={purchase_flow.get('step')}, data={purchase_flow}")
            try:
                result_state = await self.purchase_flow_node.execute(state)
                state.update(result_state)
                yield {"type": "content", "delta": state.get("response", "")}
                yield {"type": "end", "status": "success", "quick_actions": state.get("quick_actions")}
                return
            except Exception as e:
                logger.error(f"购买流程执行失败: {e}")
                yield {"type": "content", "delta": "抱歉，购买流程出现了问题，请重新开始。"}
                yield {"type": "end", "status": "error"}
                return

        aftersales_flow = state.get("aftersales_flow")
        if aftersales_flow:
            logger.info(f"🔄 [generate_response_stream] 检测到售后流程, step={aftersales_flow.get('step')}")
            try:
                result_state = await self.aftersales_flow_node.execute(state)
                state.update(result_state)
                yield {"type": "content", "delta": state.get("response", "")}
                yield {"type": "end", "status": "success", "quick_actions": state.get("quick_actions")}
                return
            except Exception as e:
                logger.error(f"售后流程执行失败: {e}")
                yield {"type": "content", "delta": "抱歉，售后流程出现了问题，请重新开始。"}
                yield {"type": "end", "status": "error"}
                return

        # Agent 节点：跳过 function_calling，直接进入 Agent 自己的工具调用循环
        if state.get("intent") == "推荐":
            logger.info("🤖 [generate_response_stream] 走 Agent 路径，跳过 function_calling")
            try:
                async for token in self.topic_advisor_node.execute_stream(state):
                    yield {"type": "content", "delta": token}
            except Exception as e:
                logger.error(f"Agent 流式执行失败: {e}")
                yield {"type": "content", "delta": "抱歉，处理您的请求时出现了问题，请稍后再试。"}
            try:
                await self.save_context_node.execute(state)
            except Exception:
                pass
            yield {
                "type": "end",
                "quick_actions": state.get("quick_actions"),
                "recommended_products": state.get("recommended_products"),
            }
            return

        t0 = time.time()
        state = await self.function_calling_node.execute(state)
        logger.info(f"⏱️ [function_calling_node] {time.time() - t0:.2f}s")

        route = self.router.route_after_function_calling(state)
        logger.info(f"⏱️ [route] → {route}")

        # 支持流式的节点使用 execute_stream
        stream_node_map = {
            "qa_flow": self.qa_node,
            "document_analysis": self.document_node,
            "purchase_guide": self.purchase_guide_node,
            "clarify": self.clarify_node,
            "topic_advisor": self.topic_advisor_node,
        }

        # 非流式节点
        node_map = {
            "product_inquiry": self.product_inquiry_node,
            "order_query": self.order_query_node,
            "ticket_flow": self.ticket_node,
            "aftersales_flow": self.aftersales_flow_node,
        }

        t0 = time.time()
        if route in stream_node_map:
            node = stream_node_map[route]
            try:
                async for token in node.execute_stream(state):
                    yield {"type": "content", "delta": token}
            except Exception as e:
                logger.error(f"流式生成失败: {e}")
                state["response"] = "抱歉，处理您的请求时出现了问题，请稍后再试。"
                yield {"type": "content", "delta": state["response"]}
        else:
            node = node_map.get(route, self.qa_node)
            try:
                result_state = await node.execute(state)
                state.update(result_state)
            except Exception as e:
                logger.error(f"节点执行失败: {e}")
                state["response"] = "抱歉，处理您的请求时出现了问题，请稍后再试。"
            if state.get("response"):
                yield {"type": "content", "delta": state["response"]}
        logger.info(f"⏱️ [{route} 节点] {time.time() - t0:.2f}s")

        t0 = time.time()
        if route != "clarify":
            try:
                await self.save_context_node.execute(state)
            except Exception:
                pass
        logger.info(f"⏱️ [save_context_node] {time.time() - t0:.2f}s")

        yield {
            "type": "end",
            "sources": state.get("sources"),
            "quick_actions": state.get("quick_actions"),
            "recommended_products": state.get("recommended_products"),
        }

    async def process_message_stream(self, user_id, session_id, message, attachments=None):
        """流式处理（兼容旧接口）"""
        start_time = datetime.now()
        
        state = await self.prepare_intent(user_id, session_id, message, attachments)
        yield {"type": "intent", "intent": state.get("intent", "问答")}
        
        state = await self.generate_response(state)
        
        if state.get("response"):
            yield {"type": "content", "delta": state["response"]}
        
        total_time = (datetime.now() - start_time).total_seconds()
        yield {
            "type": "end",
            "sources": state.get("sources"),
            "quick_actions": state.get("quick_actions"),
            "recommended_products": state.get("recommended_products"),
            "processing_time": total_time
        }


# 全局工作流实例
ai_workflow = AIWorkflow()
