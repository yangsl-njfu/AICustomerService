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
    ProductRecommendationNode,
    ProductInquiryNode,
    OrderQueryNode,
    PurchaseGuideNode
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
        self.product_recommendation_node = ProductRecommendationNode(self.llm)
        self.product_inquiry_node = ProductInquiryNode(self.llm)
        self.order_query_node = OrderQueryNode(self.llm)
        self.purchase_guide_node = PurchaseGuideNode(self.llm)
        
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
        workflow.add_node("product_recommendation", self.product_recommendation_node.execute)
        workflow.add_node("product_inquiry", self.product_inquiry_node.execute)
        workflow.add_node("order_query", self.order_query_node.execute)
        workflow.add_node("purchase_guide", self.purchase_guide_node.execute)

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
                "product_recommendation": "product_recommendation",
                "product_inquiry": "product_inquiry",
                "purchase_guide": "purchase_guide",
                "order_query": "order_query",
                "clarify": "clarify"
            }
        )
        
        workflow.add_edge("qa_flow", "save_context")
        workflow.add_edge("ticket_flow", "save_context")
        workflow.add_edge("document_analysis", "save_context")
        workflow.add_edge("product_recommendation", "save_context")
        workflow.add_edge("product_inquiry", "save_context")
        workflow.add_edge("purchase_guide", "save_context")
        workflow.add_edge("order_query", "save_context")
        workflow.add_edge("clarify", END)
        workflow.add_edge("save_context", END)
        
        return workflow.compile()
    
    def _make_initial_state(self, user_id, session_id, message, attachments):
        return ConversationState(
            user_message=message, user_id=user_id, session_id=session_id,
            attachments=attachments, conversation_history=[], user_profile={},
            intent=None, confidence=None, retrieved_docs=None,
            tool_result=None, tool_used=None, response="",
            sources=None, ticket_id=None, recommended_products=None,
            quick_actions=None, timestamp="", processing_time=None,
            intent_history=[], conversation_summary=""
        )

    async def process_message(self, user_id, session_id, message, attachments=None):
        """处理用户消息（非流式）"""
        start_time = datetime.now()
        initial_state = self._make_initial_state(user_id, session_id, message, attachments)
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
        total_start = time.time()
        state = self._make_initial_state(user_id, session_id, message, attachments)

        t0 = time.time()
        state = await self.context_node.execute(state)
        print(f"⏱️ [context_node] {time.time() - t0:.2f}s", flush=True)

        t0 = time.time()
        state = await self.intent_node.execute(state)
        print(f"⏱️ [intent_node] {time.time() - t0:.2f}s  → intent={state.get('intent')}", flush=True)

        print(f"⏱️ [prepare_intent 总计] {time.time() - total_start:.2f}s", flush=True)
        return state

    async def generate_response(self, state):
        """阶段2: function calling + 路由 + 生成回答，返回 state"""
        state = await self.function_calling_node.execute(state)
        route = self.router.route_after_function_calling(state)
        
        node_map = {
            "product_recommendation": self.product_recommendation_node,
            "product_inquiry": self.product_inquiry_node,
            "order_query": self.order_query_node,
            "clarify": self.clarify_node,
            "qa_flow": self.qa_node,
            "ticket_flow": self.ticket_node,
            "document_analysis": self.document_node,
            "purchase_guide": self.purchase_guide_node,
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
        t0 = time.time()
        state = await self.function_calling_node.execute(state)
        print(f"⏱️ [function_calling_node] {time.time() - t0:.2f}s", flush=True)

        route = self.router.route_after_function_calling(state)
        print(f"⏱️ [route] → {route}", flush=True)

        # 支持流式的节点使用 execute_stream
        stream_node_map = {
            "qa_flow": self.qa_node,
            "document_analysis": self.document_node,
            "purchase_guide": self.purchase_guide_node,
            "clarify": self.clarify_node,
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
            node_map = {
                "product_recommendation": self.product_recommendation_node,
                "product_inquiry": self.product_inquiry_node,
                "order_query": self.order_query_node,
                "ticket_flow": self.ticket_node,
            }
            node = node_map.get(route, self.qa_node)
            try:
                result_state = await node.execute(state)
                state.update(result_state)
            except Exception as e:
                logger.error(f"节点执行失败: {e}")
                state["response"] = "抱歉，处理您的请求时出现了问题，请稍后再试。"
            if state.get("response"):
                yield {"type": "content", "delta": state["response"]}
        print(f"⏱️ [{route} 节点] {time.time() - t0:.2f}s", flush=True)

        t0 = time.time()
        if route != "clarify":
            try:
                await self.save_context_node.execute(state)
            except Exception:
                pass
        print(f"⏱️ [save_context_node] {time.time() - t0:.2f}s", flush=True)

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
