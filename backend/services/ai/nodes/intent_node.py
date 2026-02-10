"""
意图识别节点 - 简单一问一答，用 LangChain ainvoke
"""
import logging
import hashlib
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseNode
from ..state import ConversationState

logger = logging.getLogger(__name__)

VALID_INTENTS = {"问答", "工单", "商品推荐", "商品咨询", "购买指导", "订单查询", "文档分析"}

SYSTEM_PROMPT = """只输出一个意图标签，不要输出任何其他内容。

标签：问答|工单|商品推荐|商品咨询|购买指导|订单查询|文档分析

规则：
- 问答：闲聊、一般咨询、平台介绍
- 工单：投诉、报错、故障、退款退货
- 商品推荐：找商品、求推荐
- 商品咨询：问某个具体商品的详情/技术栈/价格
- 购买指导：怎么买、支付方式、下单流程
- 订单查询：查订单、物流、发货
- 文档分析：上传文件需要分析

示例：
"有没有vue+springboot的毕业设计"→商品推荐
"这个项目用的什么技术栈"→商品咨询
"我的订单到哪了"→订单查询
"怎么购买"→购买指导
"买的东西质量不好想退"→工单
"你好"→问答
"推荐几个python相关的项目"→商品推荐
"发货了吗"→订单查询
"支持什么支付方式"→购买指导
"系统报错了打不开"→工单
"你们平台是做什么的"→问答"""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{message}")
])


class IntentRecognitionNode(BaseNode):
    """意图识别节点 - 直接用 LangChain ainvoke，和其他节点保持一致"""

    _intent_cache = {}
    _cache_max_size = 1000

    async def execute(self, state: ConversationState) -> ConversationState:
        has_attachments = state.get("attachments") and len(state["attachments"]) > 0
        user_message = state["user_message"].strip()

        # 附件快捷判断
        if has_attachments and len(user_message) < 20:
            state["intent"] = "文档分析"
            state["confidence"] = 0.95
            logger.info("⚡ 快速识别: 文档分析 (附件)")
            return state

        # 缓存
        cache_key = hashlib.md5(user_message.lower().encode()).hexdigest()
        if cache_key in self._intent_cache:
            cached = self._intent_cache[cache_key]
            state["intent"] = cached["intent"]
            state["confidence"] = cached["confidence"]
            logger.info(f"💾 缓存命中: {cached['intent']}")
            return state

        # 用 LangChain ainvoke，和 qa_node 等其他节点一样
        try:
            response = await self.llm.ainvoke(
                PROMPT.format_messages(message=user_message[:200])
            )
            raw = response.content.strip().strip("\"'""''")

            intent = "问答"
            for valid in VALID_INTENTS:
                if valid in raw:
                    intent = valid
                    break

            state["intent"] = intent
            state["confidence"] = 0.9
            logger.info(f"🤖 意图识别: {intent} (原始: {raw})")

        except Exception as e:
            logger.warning(f"意图识别异常，降级为问答: {e}")
            state["intent"] = "问答"
            state["confidence"] = 0.5

        # 缓存结果
        if len(self._intent_cache) >= self._cache_max_size:
            keys_to_remove = list(self._intent_cache.keys())[:self._cache_max_size // 2]
            for k in keys_to_remove:
                del self._intent_cache[k]
        self._intent_cache[cache_key] = {"intent": state["intent"], "confidence": state["confidence"]}

        return state
