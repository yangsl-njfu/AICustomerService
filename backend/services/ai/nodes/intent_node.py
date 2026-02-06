"""
意图识别节点
"""
import logging
import json
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class IntentRecognitionNode(BaseNode):
    """意图识别节点 - 使用关键词快速匹配 + LLM兜底"""
    
    # 关键词映射
    RECOMMENDATION_KEYWORDS = [
        "推荐", "有什么", "有哪些", "帮我找", "帮我推荐", "给我推荐",
        "想要", "想做", "需要", "找个", "找一个", "有没有",
        "什么项目", "什么作品", "毕业设计"
    ]
    
    INQUIRY_KEYWORDS = [
        "vue", "react", "angular", "java", "python", "spring", "django",
        "node", "mysql", "redis", "mongodb", "前后端", "微服务",
        "小程序", "app", "移动", "web", "管理系统", "电商", "商城"
    ]
    
    ORDER_KEYWORDS = [
        "订单", "物流", "快递", "发货", "到货", "ord", "配送"
    ]
    
    PURCHASE_KEYWORDS = [
        "怎么买", "如何购买", "购买流程", "支付", "付款", "退款", "售后"
    ]
    
    TICKET_KEYWORDS = [
        "投诉", "问题", "bug", "错误", "不能用", "打不开", "报错"
    ]
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行意图识别"""
        has_attachments = state.get("attachments") and len(state["attachments"]) > 0
        user_message = state["user_message"].strip().lower()

        # 如果用户上传了附件，且消息很短，自动识别为文档分析
        if has_attachments and len(user_message) < 20:
            state["intent"] = "文档分析"
            state["confidence"] = 0.95
            logger.info("快速识别: 文档分析")
            return state

        # ========== 关键词快速匹配 ==========
        # 订单查询
        if any(keyword in user_message for keyword in self.ORDER_KEYWORDS):
            state["intent"] = "订单查询"
            state["confidence"] = 0.9
            logger.info("快速识别: 订单查询")
            return state
        
        # 购买指导
        if any(keyword in user_message for keyword in self.PURCHASE_KEYWORDS):
            state["intent"] = "购买指导"
            state["confidence"] = 0.9
            logger.info("快速识别: 购买指导")
            return state
        
        # 工单
        if any(keyword in user_message for keyword in self.TICKET_KEYWORDS):
            state["intent"] = "工单"
            state["confidence"] = 0.85
            logger.info("快速识别: 工单")
            return state
        
        # 商品推荐 vs 商品咨询的判断
        has_recommendation_keyword = any(keyword in user_message for keyword in self.RECOMMENDATION_KEYWORDS)
        has_inquiry_keyword = any(keyword in user_message for keyword in self.INQUIRY_KEYWORDS)
        
        if has_recommendation_keyword:
            state["intent"] = "商品推荐"
            state["confidence"] = 0.9
            logger.info("快速识别: 商品推荐")
            return state
        
        if has_inquiry_keyword:
            state["intent"] = "商品咨询"
            state["confidence"] = 0.85
            logger.info("快速识别: 商品咨询")
            return state
        
        # ========== LLM兜底识别 ==========
        logger.info("使用LLM进行意图识别")
        
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
