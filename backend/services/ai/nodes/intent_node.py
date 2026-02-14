"""
意图识别节点 - 简单一问一答，用 LangChain ainvoke
支持多轮对话意图追踪：利用意图历史辅助当前分类，低置信度时回退到历史高置信度意图
"""
import logging
import hashlib
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseNode
from ..state import ConversationState
from config import settings

logger = logging.getLogger(__name__)

VALID_INTENTS = {"问答", "工单", "商品推荐", "个性化推荐", "商品咨询", "购买指导", "订单查询", "文档分析"}

SYSTEM_PROMPT = """只输出一个意图标签，不要输出任何其他内容。

标签：问答|工单|商品推荐|个性化推荐|商品咨询|购买指导|订单查询|文档分析

【关键区分】
- 商品推荐：用户明确说了要找什么（带技术关键词，如"推荐python项目""推荐java毕业设计"）
- 个性化推荐：用户没说自己要什么，让我推荐（如"有什么推荐""猜我喜欢""根据我的浏览推荐"）

详细规则：
- 问答：闲聊、一般咨询、平台介绍
- 工单：投诉、报错、故障、退款退货
- 商品推荐：找商品、求推荐（必须带具体技术关键词，如python/java/vue等）
- 个性化推荐：根据我的浏览历史推荐、猜我喜欢、有什么推荐（用户没说具体要什么）
- 商品咨询：问某个具体商品的详情/技术栈/价格
- 购买指导：怎么买、支付方式、下单流程
- 订单查询：查订单、物流、发货
- 文档分析：上传文件需要分析

示例：
"有没有vue+springboot的毕业设计"→商品推荐（有vue+springboot关键词）
"有什么推荐"→个性化推荐（用户没说要什么）
"根据我的浏览推荐几个"→个性化推荐
"猜我喜欢什么"→个性化推荐
"推荐几个项目"→个性化推荐（没具体关键词）
"这个项目用的什么技术栈"→商品咨询
"我的订单到哪了"→订单查询
"怎么购买"→购买指导
"买的东西质量不好想退"→工单
"你好"→问答
"推荐几个python相关的项目"→商品推荐（有python关键词）
"发货了吗"→订单查询
"支持什么支付方式"→购买指导
"系统报错了打不开"→工单
"你们平台是做什么的"→问答"""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{message}")
])

SYSTEM_PROMPT_WITH_HISTORY = """只输出一个意图标签，不要输出任何其他内容。

标签：问答|工单|商品推荐|个性化推荐|商品咨询|购买指导|订单查询|文档分析

最近的意图历史（从旧到新）：
{intent_history}

【关键区分】
- 商品推荐：用户明确说了要找什么（带技术关键词，如"推荐python项目""推荐java毕业设计"）
- 个性化推荐：用户没说自己要什么，让我推荐（如"有什么推荐""猜我喜欢""根据我的浏览推荐"）

规则：
- 如果用户消息意图明确，直接输出对应标签
- 如果用户消息意图模糊，参考最近的意图历史推断
- 如果用户明确切换话题，输出新话题的标签
- 问答：闲聊、一般咨询、平台介绍
- 工单：投诉、报错、故障、退款退货
- 商品推荐：找商品、求推荐（必须带具体技术关键词，如python/java/vue等）
- 个性化推荐：根据我的浏览历史推荐、猜我喜欢、有什么推荐（用户没说具体要什么）
- 商品咨询：问某个具体商品的详情/技术栈/价格
- 购买指导：怎么买、支付方式、下单流程
- 订单查询：查订单、物流、发货
- 文档分析：上传文件需要分析

示例：
"有没有vue+springboot的毕业设计"→商品推荐（有vue+springboot关键词）
"有什么推荐"→个性化推荐（用户没说要什么）
"根据我的浏览推荐几个"→个性化推荐
"猜我喜欢什么"→个性化推荐
"推荐几个项目"→个性化推荐（没具体关键词）
"这个项目用的什么技术栈"→商品咨询
"我的订单到哪了"→订单查询
"怎么购买"→购买指导
"买的东西质量不好想退"→工单
"你好"→问答
"推荐几个python相关的项目"→商品推荐（有python关键词）
"发货了吗"→订单查询
"支持什么支付方式"→购买指导
"系统报错了打不开"→工单
"你们平台是做什么的"→问答"""

PROMPT_WITH_HISTORY = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT_WITH_HISTORY),
    ("human", "{message}")
])


def _format_intent_history(intent_history: list, max_entries: int) -> str:
    """Format intent history entries for inclusion in the prompt.
    
    Takes the most recent `max_entries` from intent_history and formats them
    as a readable string for the LLM prompt.
    """
    if not intent_history:
        return "（无历史记录）"
    
    # Take only the most recent N entries
    recent = intent_history[-max_entries:]
    
    lines = []
    for entry in recent:
        intent = entry.get("intent", "未知")
        confidence = entry.get("confidence", 0.0)
        turn = entry.get("turn", 0)
        lines.append(f"第{turn}轮: {intent} (置信度: {confidence:.1f})")
    
    return "\n".join(lines)


def _find_fallback_intent(intent_history: list, threshold: float) -> str | None:
    """Find the most recent high-confidence intent from history for fallback.
    
    Searches intent_history from newest to oldest, returning the first intent
    with confidence >= threshold. Returns None if no qualifying entry is found.
    """
    for entry in reversed(intent_history):
        if entry.get("confidence", 0.0) >= threshold:
            return entry["intent"]
    return None


class IntentRecognitionNode(BaseNode):
    """意图识别节点 - 规则+LLM双层结构"""

    _intent_cache = {}
    _cache_max_size = 1000

    INTENT_RULES = {
        "订单查询": [
            "订单", "物流", "发货", "到了吗", "快递",
            "什么时候发", "查订单", "订单号"
        ],
        "购买指导": [
            "怎么买", "如何购买", "支付", "付款", "下单",
            "价格多少", "多少钱", "购买流程"
        ],
        "工单": [
            "投诉", "退款", "退货", "售后", "报错", "bug",
            "故障", "打不开", "不能用", "质量问题"
        ],
        "商品咨询": [
            "技术栈", "用的什么", "哪个技术", "这个项目",
            "详情", "功能", "包含什么"
        ],
        "问答": [
            "你好", "hello", "hi", "你们是", "平台",
            "做什么", "介绍", "是什么"
        ]
    }

    def _match_by_rules(self, message: str) -> tuple[str, float] | None:
        """用关键词规则匹配意图，返回 (意图, 置信度) 或 None"""
        message_lower = message.lower()
        
        # 检查其他意图
        for intent, keywords in self.INTENT_RULES.items():
            for keyword in keywords:
                if keyword in message_lower:
                    logger.info(f"⚡ 规则匹配: {intent} (关键词: {keyword})")
                    return intent, 0.95
        return None

    async def execute(self, state: ConversationState) -> ConversationState:
        has_attachments = state.get("attachments") and len(state["attachments"]) > 0
        user_message = state["user_message"].strip()
        intent_history = state.get("intent_history") or []

        # 附件快捷判断
        if has_attachments and len(user_message) < 20:
            state["intent"] = "文档分析"
            state["confidence"] = 0.95
            logger.info("⚡ 快速识别: 文档分析 (附件)")
            # Append to intent history
            self._append_intent_history(state, intent_history, "文档分析", 0.95)
            return state

        # 【第一层】规则匹配
        rule_result = self._match_by_rules(user_message)
        if rule_result:
            state["intent"] = rule_result[0]
            state["confidence"] = rule_result[1]
            logger.info(f"⚡ 规则识别: {rule_result[0]} (置信度: {rule_result[1]})")
            self._append_intent_history(state, intent_history, rule_result[0], rule_result[1])
            return state

        # 缓存
        cache_key = hashlib.md5(user_message.lower().encode()).hexdigest()
        if cache_key in self._intent_cache:
            cached = self._intent_cache[cache_key]
            state["intent"] = cached["intent"]
            state["confidence"] = cached["confidence"]
            logger.info(f"💾 缓存命中: {cached['intent']}")
            # Append to intent history even on cache hit
            self._append_intent_history(state, intent_history, cached["intent"], cached["confidence"])
            return state

        # 用 LangChain ainvoke，和 qa_node 等其他节点一样
        try:
            # Choose prompt based on whether we have intent history
            if intent_history:
                history_text = _format_intent_history(
                    intent_history, settings.INTENT_HISTORY_SIZE
                )
                messages = PROMPT_WITH_HISTORY.format_messages(
                    intent_history=history_text,
                    message=user_message[:200]
                )
            else:
                messages = PROMPT.format_messages(message=user_message[:200])

            response = await self.llm.ainvoke(messages)
            raw = response.content.strip().strip("\"'""''")

            intent = "问答"
            for valid in VALID_INTENTS:
                if valid in raw:
                    intent = valid
                    break

            confidence = 0.9
            state["intent"] = intent
            state["confidence"] = confidence
            logger.info(f"🤖 意图识别: {intent} (原始: {raw})")

            # Fallback logic: if confidence is below threshold, use recent high-confidence intent
            if confidence < settings.INTENT_FALLBACK_THRESHOLD and intent_history:
                fallback_intent = _find_fallback_intent(
                    intent_history, settings.INTENT_FALLBACK_THRESHOLD
                )
                if fallback_intent:
                    logger.info(
                        f"🔄 置信度 {confidence} 低于阈值 {settings.INTENT_FALLBACK_THRESHOLD}，"
                        f"回退到历史意图: {fallback_intent}"
                    )
                    state["intent"] = fallback_intent
                    # Keep the original low confidence to indicate this was a fallback

        except Exception as e:
            logger.warning(f"意图识别异常，降级为问答: {e}")
            state["intent"] = "问答"
            state["confidence"] = 0.5

        # Append to intent history
        self._append_intent_history(
            state, intent_history, state["intent"], state["confidence"]
        )

        # 缓存结果
        if len(self._intent_cache) >= self._cache_max_size:
            keys_to_remove = list(self._intent_cache.keys())[:self._cache_max_size // 2]
            for k in keys_to_remove:
                del self._intent_cache[k]
        self._intent_cache[cache_key] = {"intent": state["intent"], "confidence": state["confidence"]}

        return state

    def _append_intent_history(
        self,
        state: ConversationState,
        intent_history: list,
        intent: str,
        confidence: float,
    ) -> None:
        """Append a new intent entry to the intent history in state."""
        # Calculate turn number: next turn after the last entry
        turn = (intent_history[-1]["turn"] + 1) if intent_history else 1

        new_entry = {
            "intent": intent,
            "confidence": confidence,
            "turn": turn,
            "timestamp": datetime.now().isoformat(),
        }
        # Create a new list to avoid mutating the original
        updated_history = intent_history + [new_entry]
        state["intent_history"] = updated_history
