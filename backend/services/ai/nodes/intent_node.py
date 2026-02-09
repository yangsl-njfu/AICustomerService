"""
意图识别节点
"""
import logging
import json
import hashlib
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class IntentRecognitionNode(BaseNode):
    """意图识别节点 - 使用关键词快速匹配 + LLM兜底"""
    
    # 简单的内存缓存（生产环境建议使用Redis）
    _intent_cache = {}
    _cache_max_size = 1000
    
    # 关键词映射（扩展更多关键词以提高匹配率）
    RECOMMENDATION_KEYWORDS = [
        "推荐", "有什么", "有哪些", "帮我找", "帮我推荐", "给我推荐",
        "想要", "想做", "需要", "找个", "找一个", "有没有",
        "什么项目", "什么作品", "毕业设计", "适合", "好的项目",
        "求推荐", "推荐一下", "推荐个", "给推荐", "帮忙推荐"
    ]
    
    INQUIRY_KEYWORDS = [
        "vue", "react", "angular", "java", "python", "spring", "django",
        "node", "mysql", "redis", "mongodb", "前后端", "微服务",
        "小程序", "app", "移动", "web", "管理系统", "电商", "商城",
        "技术栈", "用什么", "怎么实现", "功能", "价格", "多少钱",
        "flask", "express", "laravel", "php", "golang", "rust",
        "postgresql", "oracle", "docker", "kubernetes", "云服务"
    ]
    
    ORDER_KEYWORDS = [
        "订单", "物流", "快递", "发货", "到货", "配送", "追踪",
        "我的订单", "查订单", "订单状态", "什么时候到",
        "发货了吗", "物流信息", "快递单号", "配送进度"
    ]
    
    PURCHASE_KEYWORDS = [
        "怎么买", "如何购买", "购买流程", "支付", "付款", "退款", "售后",
        "怎么付", "支付方式", "能退吗", "退货",
        "下单", "购买", "买", "付费", "收费", "免费"
    ]
    
    TICKET_KEYWORDS = [
        "投诉", "问题", "bug", "错误", "不能用", "打不开", "报错",
        "反馈", "建议", "有问题",
        "故障", "异常", "失败", "无法", "不行", "坏了"
    ]
    
    # 问答关键词（常见问题）
    QA_KEYWORDS = [
        "是什么", "什么是", "怎么", "如何", "为什么", "能不能",
        "可以", "介绍", "说明", "解释", "帮助",
        "了解", "知道", "告诉", "请问", "想问"
    ]
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行意图识别 - 优先使用快速规则匹配"""
        has_attachments = state.get("attachments") and len(state["attachments"]) > 0
        user_message = state["user_message"].strip().lower()
        
        # 生成缓存key
        cache_key = hashlib.md5(user_message.encode()).hexdigest()
        
        # 检查缓存
        if cache_key in self._intent_cache:
            cached = self._intent_cache[cache_key]
            state["intent"] = cached["intent"]
            state["confidence"] = cached["confidence"]
            logger.info(f"💾 缓存命中: {cached['intent']}")
            return state

        # ========== 快速规则匹配（优先级从高到低）==========
        
        # 1. 如果用户上传了附件，且消息很短，自动识别为文档分析
        if has_attachments and len(user_message) < 20:
            state["intent"] = "文档分析"
            state["confidence"] = 0.95
            logger.info("⚡ 快速识别: 文档分析 (附件)")
            return state

        # 2. 订单查询（高优先级）
        if any(keyword in user_message for keyword in self.ORDER_KEYWORDS):
            state["intent"] = "订单查询"
            state["confidence"] = 0.92
            logger.info("⚡ 快速识别: 订单查询")
            return state
        
        # 3. 购买指导
        if any(keyword in user_message for keyword in self.PURCHASE_KEYWORDS):
            state["intent"] = "购买指导"
            state["confidence"] = 0.90
            logger.info("⚡ 快速识别: 购买指导")
            return state
        
        # 4. 工单
        if any(keyword in user_message for keyword in self.TICKET_KEYWORDS):
            state["intent"] = "工单"
            state["confidence"] = 0.88
            logger.info("⚡ 快速识别: 工单")
            return state
        
        # 5. 商品推荐 vs 商品咨询的判断
        has_recommendation_keyword = any(keyword in user_message for keyword in self.RECOMMENDATION_KEYWORDS)
        has_inquiry_keyword = any(keyword in user_message for keyword in self.INQUIRY_KEYWORDS)
        
        if has_recommendation_keyword:
            state["intent"] = "商品推荐"
            state["confidence"] = 0.90
            logger.info("⚡ 快速识别: 商品推荐")
            return state
        
        if has_inquiry_keyword:
            state["intent"] = "商品咨询"
            state["confidence"] = 0.87
            logger.info("⚡ 快速识别: 商品咨询")
            return state
        
        # 6. 问答关键词匹配
        if any(keyword in user_message for keyword in self.QA_KEYWORDS):
            state["intent"] = "问答"
            state["confidence"] = 0.80
            logger.info("⚡ 快速识别: 问答 (问答关键词)")
            return state
        
        # 7. 如果消息很短且没有匹配到关键词，默认为问答（避免LLM调用）
        if len(user_message) < 10:
            state["intent"] = "问答"
            state["confidence"] = 0.75
            logger.info("⚡ 快速识别: 问答 (短消息默认)")
            return state
        
        # ========== LLM兜底识别（仅在必要时使用）==========
        logger.info("🤖 使用LLM进行意图识别 (规则未匹配)")
        
        # 使用原始配置（测试证明这是最快的）
        # 关键：明确的JSON格式要求让模型知道何时停止生成
        prompt = ChatPromptTemplate.from_messages([
            ("system", """识别用户意图，只返回JSON格式。

意图类型：问答、工单、商品推荐、商品咨询、购买指导、订单查询、文档分析

返回格式：{{"intent": "意图"}}"""),
            ("human", "{message}")
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(message=state["user_message"][:200])
        )

        try:
            # 尝试解析JSON
            result = json.loads(response.content)
            state["intent"] = result.get("intent", "问答")
            state["confidence"] = 0.7
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试从文本中提取
            content = response.content.strip()
            if "商品推荐" in content:
                state["intent"] = "商品推荐"
            elif "商品咨询" in content:
                state["intent"] = "商品咨询"
            elif "订单查询" in content:
                state["intent"] = "订单查询"
            elif "购买指导" in content:
                state["intent"] = "购买指导"
            elif "工单" in content:
                state["intent"] = "工单"
            elif "文档分析" in content:
                state["intent"] = "文档分析"
            else:
                state["intent"] = "问答"
            state["confidence"] = 0.6
        
        # 保存到缓存
        self._save_to_cache(cache_key, state["intent"], state["confidence"])

        return state
    
    def _save_to_cache(self, key: str, intent: str, confidence: float):
        """保存到缓存"""
        # 如果缓存满了，清除最旧的一半
        if len(self._intent_cache) >= self._cache_max_size:
            keys_to_remove = list(self._intent_cache.keys())[:self._cache_max_size // 2]
            for k in keys_to_remove:
                del self._intent_cache[k]
        
        self._intent_cache[key] = {
            "intent": intent,
            "confidence": confidence
        }
