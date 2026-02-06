"""
AI工作流编排器
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from config import settings

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


class AIWorkflow:
    """AI工作流编排器"""
    
    def __init__(self):
        # 初始化LLM
        if settings.LLM_PROVIDER == "deepseek":
            self.llm = ChatOpenAI(
                model=settings.DEEPSEEK_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
        
        # 初始化路由器
        self.router = Router()
        
        # 初始化所有节点
        self.context_node = ContextNode()
        self.intent_node = IntentRecognitionNode(self.llm)
        self.function_calling_node = FunctionCallingNode(self.llm)
        self.save_context_node = SaveContextNode()
        self.qa_node = QANode(self.llm)
        self.document_node = DocumentNode(self.llm)
        self.ticket_node = TicketNode(self.llm)
        self.clarify_node = ClarifyNode(self.llm)
        self.product_recommendation_node = ProductRecommendationNode(self.llm)
        self.product_inquiry_node = ProductInquiryNode(self.llm)
        self.order_query_node = OrderQueryNode(self.llm)
        self.purchase_guide_node = PurchaseGuideNode(self.llm)
        
        # 构建工作流图
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """构建工作流图"""
        workflow = StateGraph(ConversationState)
        
        # 添加所有节点
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
        
        # 设置入口点
        workflow.set_entry_point("load_context")
        
        # 添加边
        workflow.add_edge("load_context", "intent_recognition")
        workflow.add_edge("intent_recognition", "function_calling")
        
        # 添加条件边（路由）
        workflow.add_conditional_edges(
            "function_calling",
            self.router.route_after_function_calling,
            {
                "qa_flow": "qa_flow",
                "ticket_flow": "ticket_flow",
                "product_flow": "qa_flow",  # product_flow使用qa_flow
                "document_analysis": "document_analysis",
                "product_recommendation": "product_recommendation",
                "product_inquiry": "product_inquiry",
                "purchase_guide": "purchase_guide",
                "order_query": "order_query",
                "clarify": "clarify"
            }
        )
        
        # 添加结束边
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
    
    async def process_message(
        self,
        user_id: str,
        session_id: str,
        message: str,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """处理用户消息"""
        import logging
        logger = logging.getLogger(__name__)
        
        start_time = datetime.now()
        logger.info(f"开始处理消息: session_id={session_id}, message={message[:50] if message else '(empty)'}")
        
        # 初始化状态
        initial_state = ConversationState(
            user_message=message,
            user_id=user_id,
            session_id=session_id,
            attachments=attachments,
            conversation_history=[],
            user_profile={},
            intent=None,
            confidence=None,
            retrieved_docs=None,
            tool_result=None,
            tool_used=None,
            response="",
            sources=None,
            ticket_id=None,
            recommended_products=None,
            quick_actions=None,
            timestamp="",
            processing_time=None
        )
        
        # 执行工作流
        logger.info("开始执行工作流...")
        final_state = await self.graph.ainvoke(initial_state)
        logger.info(f"工作流执行完成: intent={final_state.get('intent')}")
        
        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        final_state["processing_time"] = processing_time
        
        return final_state
    
    async def process_message_stream(
        self,
        user_id: str,
        session_id: str,
        message: str,
        attachments: Optional[List[Dict]] = None
    ):
        """流式处理用户消息"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"开始流式处理: session_id={session_id}, message={message[:50]}")
        
        start_time = datetime.now()
        
        # 1. 显示开始思考
        yield {"type": "thinking", "content": "正在分析您的问题..."}
        await asyncio.sleep(0.3)
        
        # 初始化状态
        initial_state = ConversationState(
            user_message=message,
            user_id=user_id,
            session_id=session_id,
            attachments=attachments,
            conversation_history=[],
            user_profile={},
            intent=None,
            confidence=None,
            retrieved_docs=None,
            tool_result=None,
            tool_used=None,
            response="",
            sources=None,
            ticket_id=None,
            recommended_products=None,
            quick_actions=None,
            timestamp="",
            processing_time=None
        )
        
        # 2. 显示意图识别
        yield {"type": "thinking", "content": "识别意图中..."}
        await asyncio.sleep(0.2)
        
        # 执行workflow
        logger.info("执行完整workflow...")
        final_state = await self.graph.ainvoke(initial_state)
        logger.info(f"Workflow完成: intent={final_state.get('intent')}, tool_used={final_state.get('tool_used')}")
        
        # 3. 发送识别到的意图
        intent = final_state.get("intent", "问答")
        yield {"type": "intent", "intent": intent}
        yield {"type": "thinking", "content": f"识别到意图: {intent}"}
        await asyncio.sleep(0.2)
        
        # 4. 如果有工具调用,显示工具信息
        if final_state.get("tool_used"):
            tools = final_state.get("tool_used")
            yield {"type": "thinking", "content": f"正在调用工具: {tools}"}
            await asyncio.sleep(0.3)
            yield {"type": "thinking", "content": "工具调用完成,正在生成回复..."}
            await asyncio.sleep(0.2)
        else:
            yield {"type": "thinking", "content": "正在生成回复..."}
            await asyncio.sleep(0.2)
        
        # 5. 流式输出响应内容
        response = final_state.get("response", "")
        chunk_size = 15  # 每次输出15个字符
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i+chunk_size]
            yield {"type": "content", "delta": chunk}
            await asyncio.sleep(0.02)
        
        # 6. 发送结束事件,包含quick_actions
        end_data = {
            "type": "end",
            "sources": final_state.get("sources"),
            "quick_actions": final_state.get("quick_actions"),
            "recommended_products": final_state.get("recommended_products"),
            "processing_time": (datetime.now() - start_time).total_seconds()
        }
        yield end_data


# 全局工作流实例
ai_workflow = AIWorkflow()
