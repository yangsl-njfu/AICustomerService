"""
LangGraph对话工作流
"""
from typing import TypedDict, List, Dict, Optional, Any
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config import settings
from .knowledge_retriever import knowledge_retriever
from .redis_cache import redis_cache
from .file_service import FileService
import json

file_service = FileService()


# 定义对话状态
class ConversationState(TypedDict):
    # 输入
    user_message: str
    user_id: str
    session_id: str
    attachments: Optional[List[Dict]]
    
    # 上下文
    conversation_history: List[Dict[str, str]]
    user_profile: Dict
    
    # 处理过程
    intent: Optional[str]
    confidence: Optional[float]
    retrieved_docs: Optional[List[Dict]]
    
    # 输出
    response: str
    sources: Optional[List[Dict]]
    ticket_id: Optional[str]
    recommended_products: Optional[List[str]]
    
    # 元数据
    timestamp: str
    processing_time: Optional[float]


class LangGraphWorkflow:
    """LangGraph工作流类"""

    def __init__(self):
        # 初始化LLM（支持 OpenAI 和 DeepSeek）
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
        
        # 构建工作流图
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """构建LangGraph工作流图"""
        workflow = StateGraph(ConversationState)
        
        # 添加节点
        workflow.add_node("load_context", self.load_context_node)
        workflow.add_node("intent_recognition", self.intent_recognition_node)
        workflow.add_node("qa_flow", self.qa_flow_node)
        workflow.add_node("ticket_flow", self.ticket_flow_node)
        workflow.add_node("product_flow", self.product_flow_node)
        workflow.add_node("document_analysis", self.document_analysis_node)
        workflow.add_node("product_recommendation", self.product_recommendation_node)
        workflow.add_node("product_inquiry", self.product_inquiry_node)
        workflow.add_node("purchase_guide", self.purchase_guide_node)
        workflow.add_node("order_query", self.order_query_node)
        workflow.add_node("clarify", self.clarify_intent_node)
        workflow.add_node("save_context", self.save_context_node)

        # 设置入口点
        workflow.set_entry_point("load_context")

        # 添加边
        workflow.add_edge("load_context", "intent_recognition")

        # 添加条件边（路由）
        workflow.add_conditional_edges(
            "intent_recognition",
            self.route_decision,
            {
                "qa_flow": "qa_flow",
                "ticket_flow": "ticket_flow",
                "product_flow": "product_flow",
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
        workflow.add_edge("product_flow", "save_context")
        workflow.add_edge("document_analysis", "save_context")
        workflow.add_edge("product_recommendation", "save_context")
        workflow.add_edge("product_inquiry", "save_context")
        workflow.add_edge("purchase_guide", "save_context")
        workflow.add_edge("order_query", "save_context")
        workflow.add_edge("clarify", END)
        workflow.add_edge("save_context", END)
        
        # 编译图
        return workflow.compile()
    
    async def load_context_node(self, state: ConversationState) -> ConversationState:
        """加载会话上下文"""
        context = await redis_cache.get_context(state["session_id"])
        
        if context:
            state["conversation_history"] = context.get("history", [])
            state["user_profile"] = context.get("user_profile", {})
        else:
            state["conversation_history"] = []
            state["user_profile"] = {}
        
        state["timestamp"] = datetime.now().isoformat()
        return state
    
    async def intent_recognition_node(self, state: ConversationState) -> ConversationState:
        """意图识别节点"""
        # 检查是否有附件但没有明确指令
        has_attachments = state.get("attachments") and len(state["attachments"]) > 0
        user_message = state["user_message"].strip()

        # 如果用户上传了附件，且消息很短（没有明确问题），自动识别为文档分析
        if has_attachments and len(user_message) < 20:
            state["intent"] = "文档分析"
            state["confidence"] = 0.95
            return state

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个意图识别助手。分析用户消息并识别其意图。
可能的意图：
- 问答：用户询问问题，需要从知识库检索答案
- 工单：用户需要创建工单或查询工单状态
- 产品咨询：用户询问产品信息、价格、功能等
- 文档分析：用户上传了文档并需要分析/总结/解释
- 商品推荐：用户想要推荐毕业设计作品，询问"有什么推荐"、"帮我找个项目"等
- 商品咨询：用户询问具体商品的详情、技术栈、价格等
- 购买指导：用户询问如何购买、支付方式、退款政策等
- 订单查询：用户查询订单状态、物流信息等
- 闲聊：一般性对话

返回JSON格式：{{"intent": "意图类型", "confidence": 0.0-1.0}}"""),
            ("human", """用户消息：{message}
历史对话：{history}
是否有附件：{has_attachments}

请识别意图：""")
        ])

        history_str = json.dumps(state["conversation_history"][-5:], ensure_ascii=False)

        response = await self.llm.ainvoke(
            prompt.format_messages(
                message=state["user_message"],
                history=history_str,
                has_attachments="是" if has_attachments else "否"
            )
        )

        try:
            result = json.loads(response.content)
            state["intent"] = result.get("intent", "问答")
            state["confidence"] = result.get("confidence", 0.5)
        except json.JSONDecodeError:
            state["intent"] = "问答"
            state["confidence"] = 0.5

        return state
    
    def route_decision(self, state: ConversationState) -> str:
        """路由决策"""
        if state["confidence"] < 0.6:
            return "clarify"

        intent_map = {
            "问答": "qa_flow",
            "工单": "ticket_flow",
            "产品咨询": "product_flow",
            "文档分析": "document_analysis",
            "商品推荐": "product_recommendation",
            "商品咨询": "product_inquiry",
            "购买指导": "purchase_guide",
            "订单查询": "order_query"
        }
        return intent_map.get(state["intent"], "clarify")
    
    async def qa_flow_node(self, state: ConversationState) -> ConversationState:
        """问答流程节点"""
        # 提取附件内容
        attachment_texts = []
        if state.get("attachments"):
            for att in state["attachments"]:
                file_path = att.get("file_path", "")
                if file_path:
                    text = file_service.extract_text(file_path)
                    if text:
                        attachment_texts.append(f"【附件：{att.get('file_name', '未知文件')}】\n{text[:5000]}")  # 限制长度

        # 检索相关文档
        docs = await knowledge_retriever.retrieve(
            query=state["user_message"],
            collection_name="knowledge_base",
            top_k=settings.RETRIEVAL_TOP_K
        )

        state["retrieved_docs"] = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in docs
        ]

        # 生成回答
        docs_text = "\n\n".join([
            f"文档{i+1}：{doc.page_content}"
            for i, doc in enumerate(docs)
        ])

        # 合并附件内容
        attachment_content = "\n\n".join(attachment_texts) if attachment_texts else "无附件"

        history_str = "\n".join([
            f"用户：{turn['user']}\n助手：{turn['assistant']}"
            for turn in state["conversation_history"][-3:]
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的AI客服助手。基于提供的知识库内容和用户上传的附件回答用户问题。
要求：
1. 优先参考用户上传的附件内容回答问题
2. 如果附件中有相关信息，详细解释附件内容
3. 如果附件中没有相关信息，再参考知识库内容
4. 回答要准确、简洁、有帮助
5. 引用知识库来源或附件名称
6. 保持友好专业的语气"""),
            ("human", """知识库内容：
{docs}

用户上传的附件内容：
{attachments}

历史对话：
{history}

用户问题：{question}

请基于附件和知识库内容回答：""")
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                docs=docs_text,
                attachments=attachment_content,
                history=history_str,
                question=state["user_message"]
            )
        )

        state["response"] = response.content
        state["sources"] = [doc.metadata for doc in docs]

        return state

    async def document_analysis_node(self, state: ConversationState) -> ConversationState:
        """文档分析节点 - 主动分析用户上传的文档"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"文档分析节点: attachments={len(state.get('attachments', []))}")
        
        # 提取附件内容
        attachment_texts = []
        attachment_names = []

        if state.get("attachments"):
            for att in state["attachments"]:
                file_path = att.get("file_path", "")
                file_name = att.get("file_name", "未知文件")
                logger.info(f"处理附件: {file_name}, path={file_path}")
                if file_path:
                    text = file_service.extract_text(file_path)
                    logger.info(f"提取文本长度: {len(text) if text else 0}")
                    if text:
                        attachment_texts.append(text[:8000])  # 限制长度
                        attachment_names.append(file_name)

        if not attachment_texts:
            logger.warning("无法提取附件内容")
            state["response"] = "我注意到您上传了文件，但无法读取文件内容。请确保文件格式正确（支持 PDF、Word、TXT 等格式）。"
            return state

        # 构建文档内容
        all_content = "\n\n---\n\n".join(attachment_texts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的文档分析助手。用户上传了文档，请主动分析并提供详细的解读。

分析要求：
1. 首先介绍文档的类型和大致内容
2. 提取文档的核心要点和关键信息
3. 总结文档的主要结论或建议
4. 如果文档有结构（如标题、章节），请按结构组织回答
5. 使用清晰的格式（标题、 bullet points 等）
6. 语言友好、专业，像在向用户汇报分析结果

不要等待用户提问，主动提供全面的文档解读。"""),
            ("human", """用户上传的文档：{file_names}

文档内容：
{content}

请提供详细的文档分析和解读：""")
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                file_names=", ".join(attachment_names),
                content=all_content
            )
        )

        state["response"] = response.content
        state["sources"] = [{"type": "attachment", "files": attachment_names}]

        return state

    async def ticket_flow_node(self, state: ConversationState) -> ConversationState:
        """工单流程节点"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个工单处理助手。从用户消息中提取工单信息。
返回JSON格式：
{
    "title": "工单标题",
    "description": "问题描述",
    "priority": "low/medium/high/urgent",
    "category": "问题类别"
}"""),
            ("human", """用户消息：{message}
历史对话：{history}

请提取工单信息：""")
        ])
        
        history_str = json.dumps(state["conversation_history"], ensure_ascii=False)
        
        response = await self.llm.ainvoke(
            prompt.format_messages(
                message=state["user_message"],
                history=history_str
            )
        )
        
        try:
            ticket_info = json.loads(response.content)
            # 这里应该调用TicketService创建工单，暂时模拟
            ticket_id = f"TK{datetime.now().strftime('%Y%m%d%H%M%S')}"
            state["ticket_id"] = ticket_id
            state["response"] = f"工单已创建成功！\n\n工单号：{ticket_id}\n标题：{ticket_info['title']}\n我们会尽快处理您的问题。"
        except json.JSONDecodeError:
            state["response"] = "抱歉，创建工单时出现问题。请提供更详细的问题描述。"
        
        return state
    
    async def product_flow_node(self, state: ConversationState) -> ConversationState:
        """产品咨询流程节点"""
        # 检索产品信息
        products = await knowledge_retriever.retrieve(
            query=state["user_message"],
            collection_name="product_catalog",
            top_k=5
        )
        
        products_text = "\n\n".join([
            f"产品{i+1}：{doc.page_content}"
            for i, doc in enumerate(products)
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个产品咨询专家。基于产品信息回答用户咨询。
要求：
1. 突出产品特点和优势
2. 提供价格信息（如果有）
3. 说明适用场景
4. 进行产品对比（如果用户询问）"""),
            ("human", """产品信息：
{products}

用户咨询：{question}

请回答：""")
        ])
        
        response = await self.llm.ainvoke(
            prompt.format_messages(
                products=products_text,
                question=state["user_message"]
            )
        )
        
        state["response"] = response.content
        state["recommended_products"] = [
            doc.metadata.get("product_id") 
            for doc in products 
            if doc.metadata.get("product_id")
        ]
        
        return state
    
    async def clarify_intent_node(self, state: ConversationState) -> ConversationState:
        """澄清意图节点 - 使用AI生成更自然的回复"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个友好的AI客服助手。用户的消息意图不够明确，请自然地询问用户需要什么帮助。
要求：
1. 回复要自然、友好，像真人对话
2. 简要列出可能的服务选项（问答、工单、产品咨询）
3. 邀请用户详细说明需求
4. 不要机械地列1、2、3，而是融入对话中"""),
            ("human", """用户消息：{message}
历史对话：{history}

请自然地询问用户需要什么帮助：""")
        ])

        history_str = "\n".join([
            f"用户：{turn['user']}\n助手：{turn['assistant']}"
            for turn in state["conversation_history"][-3:]
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                message=state["user_message"],
                history=history_str
            )
        )

        state["response"] = response.content
        return state
    
    async def save_context_node(self, state: ConversationState) -> ConversationState:
        """保存上下文节点"""
        # 添加新的对话轮次到上下文
        await redis_cache.add_message_to_context(
            session_id=state["session_id"],
            user_message=state["user_message"],
            assistant_message=state["response"]
        )
        
        # 更新最后意图
        await redis_cache.update_context(
            session_id=state["session_id"],
            last_intent=state.get("intent")
        )
        
        return state
    
    async def product_recommendation_node(self, state: ConversationState) -> ConversationState:
        """商品推荐节点"""
        # 1. 提取用户需求
        extract_prompt = ChatPromptTemplate.from_messages([
            ("system", """分析用户需求并提取关键信息。返回JSON格式：
{
    "major": "专业/方向（如：计算机、电子、管理）",
    "tech_stack": ["技术栈列表"],
    "budget": 最高预算（数字，如果没提到返回null）,
    "difficulty": "难度（easy/medium/hard，如果没提到返回null）"
}"""),
            ("human", "用户消息：{message}")
        ])
        
        response = await self.llm.ainvoke(extract_prompt.format_messages(
            message=state["user_message"]
        ))
        
        try:
            requirements = json.loads(response.content)
        except:
            requirements = {}
        
        # 2. 从数据库检索匹配商品
        from database.connection import get_db_context
        from services.product_service import ProductService
        
        async with get_db_context() as db:
            product_service = ProductService(db)
            
            # 构建搜索参数
            search_params = {
                "status": "published",
                "page": 1,
                "page_size": 5,
                "sort_by": "rating",
                "order": "desc"
            }
            
            if requirements.get("budget"):
                search_params["max_price"] = requirements["budget"]
            
            if requirements.get("difficulty"):
                search_params["difficulty"] = requirements["difficulty"]
            
            if requirements.get("tech_stack"):
                search_params["tech_stack"] = requirements["tech_stack"]
            
            result = await product_service.search_products(**search_params)
            products = result.get("products", [])
        
        # 3. 生成推荐理由
        if not products:
            state["response"] = "抱歉，暂时没有找到符合您需求的毕业设计作品。您可以调整一下需求，比如预算或难度要求。"
            return state
        
        products_text = "\n\n".join([
            f"商品{i+1}：{p['title']}\n价格：¥{p['price']}\n技术栈：{', '.join(p.get('tech_stack', []))}\n评分：{p['rating']}⭐\n销量：{p['sales_count']}"
            for i, p in enumerate(products)
        ])
        
        recommend_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是毕业设计作品推荐专家。根据用户需求推荐合适的作品。
要求：
1. 分析每个商品的特点
2. 说明为什么推荐这些商品
3. 给出选择建议
4. 语气友好、专业"""),
            ("human", """用户需求：{requirements}

可选商品：
{products}

请推荐最合适的商品并说明理由：""")
        ])
        
        response = await self.llm.ainvoke(recommend_prompt.format_messages(
            requirements=json.dumps(requirements, ensure_ascii=False),
            products=products_text
        ))
        
        state["response"] = response.content
        state["recommended_products"] = [p["id"] for p in products]
        
        return state
    
    async def product_inquiry_node(self, state: ConversationState) -> ConversationState:
        """商品咨询节点"""
        # 从用户消息中提取可能的商品ID或关键词
        from database.connection import get_db_context
        from services.product_service import ProductService
        
        async with get_db_context() as db:
            product_service = ProductService(db)
            
            # 搜索相关商品
            result = await product_service.search_products(
                keyword=state["user_message"],
                status="published",
                page=1,
                page_size=3
            )
            products = result.get("products", [])
        
        if not products:
            state["response"] = "抱歉，没有找到相关的商品。您可以换个关键词试试，或者告诉我您想要什么类型的毕业设计。"
            return state
        
        # 构建商品信息
        products_info = "\n\n".join([
            f"商品：{p['title']}\n描述：{p['description'][:200]}...\n价格：¥{p['price']}\n技术栈：{', '.join(p.get('tech_stack', []))}\n难度：{p['difficulty']}\n评分：{p['rating']}⭐"
            for p in products
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是商品咨询专家。基于商品信息回答用户问题。
要求：
1. 详细解释商品特点
2. 说明技术栈和难度
3. 解答用户疑问
4. 如果用户问价格，明确告知
5. 语气专业、友好"""),
            ("human", """商品信息：
{products}

用户问题：{question}

请详细回答：""")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages(
            products=products_info,
            question=state["user_message"]
        ))
        
        state["response"] = response.content
        state["recommended_products"] = [p["id"] for p in products]
        
        return state
    
    async def purchase_guide_node(self, state: ConversationState) -> ConversationState:
        """购买指导节点"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是购买指导专家。帮助用户了解购买流程。

平台购买流程：
1. 浏览商品，选择心仪的毕业设计作品
2. 点击"加入购物车"或"立即购买"
3. 在购物车中确认商品和价格
4. 点击"去结算"，填写订单信息
5. 选择支付方式（支持支付宝、微信支付）
6. 完成支付后，卖家会交付商品文件
7. 确认收货后可以评价

支付方式：
- 支付宝
- 微信支付

退款政策：
- 商品交付前可以取消订单，全额退款
- 商品交付后，如有质量问题可申请退款
- 退款会在3-5个工作日内到账

要求：
1. 根据用户问题提供相应指导
2. 语言简洁明了
3. 如果用户遇到具体问题，建议创建工单"""),
            ("human", "用户问题：{question}\n\n请提供购买指导：")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages(
            question=state["user_message"]
        ))
        
        state["response"] = response.content
        
        return state
    
    async def order_query_node(self, state: ConversationState) -> ConversationState:
        """订单查询节点"""
        # 获取用户订单
        from database.connection import get_db_context
        from services.order_service import OrderService
        
        async with get_db_context() as db:
            order_service = OrderService(db)
            
            # 获取用户最近的订单
            result = await order_service.list_orders(
                user_id=state["user_id"],
                page=1,
                page_size=5
            )
            orders = result.get("orders", [])
        
        if not orders:
            state["response"] = "您还没有订单记录。浏览商品后可以下单购买哦！"
            return state
        
        # 构建订单信息
        orders_info = "\n\n".join([
            f"订单号：{o['order_no']}\n总金额：¥{o['total_amount']}\n状态：{o['status']}\n创建时间：{o['created_at']}"
            for o in orders
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是订单查询助手。帮助用户了解订单状态。

订单状态说明：
- pending：待支付
- paid：已支付，等待卖家交付
- delivered：已交付，等待买家确认
- completed：已完成
- cancelled：已取消
- refunded：已退款

要求：
1. 根据用户问题提供订单信息
2. 解释订单状态
3. 如果有问题，提供解决建议"""),
            ("human", """用户订单：
{orders}

用户问题：{question}

请回答：""")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages(
            orders=orders_info,
            question=state["user_message"]
        ))
        
        state["response"] = response.content
        
        return state
    
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
        logger.info(f"开始处理消息: session_id={session_id}, message={message[:50] if message else '(empty)'}, attachments={len(attachments) if attachments else 0}")
        
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
            response="",
            sources=None,
            ticket_id=None,
            recommended_products=None,
            timestamp="",
            processing_time=None
        )
        
        # 执行工作流
        logger.info("开始执行工作流...")
        final_state = await self.graph.ainvoke(initial_state)
        logger.info(f"工作流执行完成: intent={final_state.get('intent')}, response_length={len(final_state.get('response', ''))}")
        
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
        """流式处理用户消息 - 实时生成回复"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"开始流式处理: session_id={session_id}")
        
        # 1. 加载上下文
        context = await redis_cache.get_context(session_id)
        conversation_history = context.get("history", []) if context else []
        
        # 2. 意图识别
        has_attachments = attachments and len(attachments) > 0
        if has_attachments and len(message.strip()) < 20:
            intent = "文档分析"
            confidence = 0.95
        else:
            intent = "问答"
            confidence = 0.8
        
        logger.info(f"意图识别: {intent}")
        yield {"type": "intent", "intent": intent}
        
        # 3. 输出思考过程
        thinking_content = []
        if has_attachments and attachments:
            thinking_content.append(f"用户上传了 {len(attachments)} 个文件")
            for att in attachments:
                thinking_content.append(f"- {att.get('file_name', '未知文件')}")
        thinking_content.append(f"识别到意图: {intent}")
        yield {"type": "thinking", "content": "\n".join(thinking_content)}
        
        # 4. 根据意图处理
        if intent == "文档分析":
            # 提取附件内容
            attachment_texts = []
            attachment_names = []
            
            if attachments:
                for att in attachments:
                    file_path = att.get("file_path", "")
                    file_name = att.get("file_name", "未知文件")
                    if file_path:
                        text = file_service.extract_text(file_path)
                        if text:
                            attachment_texts.append(text[:8000])
                            attachment_names.append(file_name)
            
            if not attachment_texts:
                yield {"type": "content", "delta": "我注意到您上传了文件，但无法读取文件内容。请确保文件格式正确（支持 PDF、Word、TXT 等格式）。"}
                return
            
            # 构建提示
            all_content = "\n\n---\n\n".join(attachment_texts)
            prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个专业的文档分析助手。用户上传了文档，请主动分析并提供详细的解读。"""),
                ("human", """用户上传的文档：{file_names}

文档内容：
{content}

请提供详细的文档分析和解读：""")
            ])
            
            messages = prompt.format_messages(
                file_names=", ".join(attachment_names),
                content=all_content
            )
            
            # 流式生成回复
            logger.info("开始流式生成文档分析...")
            full_response = ""
            async for chunk in self.llm.astream(messages):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if content:
                    full_response += content
                    yield {"type": "content", "delta": content}
            
            logger.info(f"流式生成完成，总长度: {len(full_response)}")
            
            # 保存上下文
            await redis_cache.update_context(
                session_id=session_id,
                last_intent=intent,
                history=conversation_history + [{"user": message, "assistant": full_response}]
            )
            
            yield {"type": "end", "sources": [{"type": "attachment", "files": attachment_names}]}
            
        else:
            # 其他意图（问答等）
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个专业的AI客服助手。"),
                ("human", "{message}")
            ])
            
            messages = prompt.format_messages(message=message)
            
            full_response = ""
            async for chunk in self.llm.astream(messages):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if content:
                    full_response += content
                    yield {"type": "content", "delta": content}
            
            yield {"type": "end", "sources": []}


# 全局工作流实例
langgraph_workflow = LangGraphWorkflow()
