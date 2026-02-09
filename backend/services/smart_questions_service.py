"""
智能快速问题推荐服务
根据用户画像、订单历史、浏览记录等智能推荐问题
"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config import settings
import json
import hashlib
from datetime import datetime, timedelta


class SmartQuestionsService:
    """智能问题推荐服务"""
    
    def __init__(self):
        # 初始化LLM
        if settings.LLM_PROVIDER == "deepseek":
            self.llm = ChatOpenAI(
                model=settings.DEEPSEEK_MODEL,
                temperature=0.7,
                max_tokens=500,
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.7,
                max_tokens=500,
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
        
        # 内存缓存 (生产环境应使用Redis)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 3600  # 缓存1小时
    
    def _get_cache_key(self, user_id: str, context: str) -> str:
        """生成缓存键"""
        # 使用用户ID和上下文的hash作为缓存键
        context_hash = hashlib.md5(context.encode()).hexdigest()[:8]
        return f"smart_questions:{user_id}:{context_hash}"
    
    def _get_cached_questions(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """从缓存获取问题"""
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # 检查是否过期
            if datetime.now() < cached["expires_at"]:
                return cached["questions"]
            else:
                # 删除过期缓存
                del self._cache[cache_key]
        return None
    
    def _set_cached_questions(self, cache_key: str, questions: List[Dict[str, Any]]):
        """设置缓存"""
        self._cache[cache_key] = {
            "questions": questions,
            "expires_at": datetime.now() + timedelta(seconds=self._cache_ttl)
        }
    
    async def generate_smart_questions(
        self,
        user_id: str,
        user_profile: Dict[str, Any],
        recent_orders: List[Dict[str, Any]] = None,
        browsing_history: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        根据用户数据智能生成快速问题
        
        Args:
            user_id: 用户ID
            user_profile: 用户画像 (偏好、兴趣等)
            recent_orders: 最近订单
            browsing_history: 浏览历史
        
        Returns:
            快速问题列表
        """
        # 构建用户上下文
        context = self._build_user_context(user_profile, recent_orders, browsing_history)
        
        # 检查缓存
        cache_key = self._get_cache_key(user_id, context)
        cached_questions = self._get_cached_questions(cache_key)
        if cached_questions:
            print(f"使用缓存的智能问题: {cache_key}")
            return cached_questions
        
        # 使用AI生成个性化问题
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能客服助手,负责为用户生成个性化的售后服务快速问题。

**客服定位**: 售后服务为主,不推荐商品

**任务**: 根据用户的订单历史、浏览记录、偏好等信息,生成4个最相关的售后服务问题。

**规则**:
1. 问题要简短(10字以内)
2. 聚焦售后服务: 订单查询、物流、退款、使用帮助、投诉建议
3. 如果用户有待收货订单,推荐"查看物流"
4. 如果用户有已完成订单,推荐"申请退款"、"联系卖家"
5. 如果是新用户,推荐基础问题: "如何购买"、"使用帮助"

**输出格式** (JSON):
{{
  "questions": [
    {{"label": "问题文本", "question": "完整问题", "icon": "emoji图标", "reason": "推荐理由"}},
    ...
  ]
}}

**示例**:
- 用户有待收货订单 → "查看物流" 📦
- 用户有已完成订单 → "如何申请退款?" 💰
- 用户是新用户 → "如何购买作品?" 🛒
- 用户购买过项目 → "使用遇到问题" ❓"""),
            ("human", """用户信息:
{context}

请生成4个个性化的售后服务问题:""")
        ])
        
        try:
            response = await self.llm.ainvoke(
                prompt.format_messages(context=context)
            )
            
            # 解析AI返回的JSON
            result = json.loads(response.content)
            questions = result.get("questions", [])
            
            # 转换为前端需要的格式
            quick_actions = []
            for q in questions[:4]:  # 最多4个
                quick_actions.append({
                    "type": "button",
                    "label": q.get("label", ""),
                    "action": "send_question",
                    "data": {"question": q.get("question", q.get("label", ""))},
                    "icon": q.get("icon", "💬")
                })
            
            # 缓存结果
            self._set_cached_questions(cache_key, quick_actions)
            
            return quick_actions
        
        except Exception as e:
            print(f"生成智能问题失败: {e}")
            # 返回基于规则的智能问题
            return self._get_rule_based_questions(recent_orders)
    
    def _build_user_context(
        self,
        user_profile: Dict[str, Any],
        recent_orders: List[Dict[str, Any]] = None,
        browsing_history: List[Dict[str, Any]] = None
    ) -> str:
        """构建用户上下文描述"""
        context_parts = []
        
        # 用户画像
        if user_profile:
            interests = user_profile.get("interests", [])
            if interests:
                context_parts.append(f"用户兴趣: {', '.join(interests)}")
            
            preferences = user_profile.get("preferences", {})
            if preferences:
                context_parts.append(f"用户偏好: {json.dumps(preferences, ensure_ascii=False)}")
        
        # 订单历史
        if recent_orders:
            order_info = []
            for order in recent_orders[:3]:  # 最近3个订单
                status = order.get("status", "")
                product_name = order.get("product_name", "")
                if status == "shipped":
                    order_info.append(f"有待收货订单: {product_name}")
                elif status == "completed":
                    order_info.append(f"已购买: {product_name}")
            
            if order_info:
                context_parts.append("订单历史:\n" + "\n".join(order_info))
        
        # 浏览历史
        if browsing_history:
            viewed_products = []
            for item in browsing_history[:5]:  # 最近5个浏览
                product_name = item.get("product_name", "")
                tech_stack = item.get("tech_stack", [])
                if product_name:
                    viewed_products.append(f"{product_name} ({', '.join(tech_stack)})")
            
            if viewed_products:
                context_parts.append("浏览历史:\n" + "\n".join(viewed_products))
        
        # 如果没有任何信息,标记为新用户
        if not context_parts:
            context_parts.append("新用户,没有历史数据")
        
        return "\n\n".join(context_parts)
    
    def _get_rule_based_questions(self, recent_orders: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """基于规则生成智能问题(快速,不需要AI)"""
        questions = []
        
        # 如果有待收货订单,优先推荐查看物流
        if recent_orders:
            for order in recent_orders[:3]:
                if order.get("status") == "shipped":
                    questions.append({
                        "type": "button",
                        "label": "查看物流信息",
                        "action": "send_question",
                        "data": {"question": "查看物流信息"},
                        "icon": "🚚"
                    })
                    break
        
        # 补充售后相关问题
        default_questions = [
            {
                "type": "button",
                "label": "订单有问题",
                "action": "send_question",
                "data": {"question": "我的订单有问题"},
                "icon": "📦"
            },
            {
                "type": "button",
                "label": "如何申请退款?",
                "action": "send_question",
                "data": {"question": "如何申请退款?"},
                "icon": "💰"
            },
            {
                "type": "button",
                "label": "如何联系卖家?",
                "action": "send_question",
                "data": {"question": "如何联系卖家?"},
                "icon": "💬"
            },
            {
                "type": "button",
                "label": "使用遇到问题",
                "action": "send_question",
                "data": {"question": "使用遇到问题怎么办?"},
                "icon": "❓"
            },
            {
                "type": "button",
                "label": "如何购买作品?",
                "action": "send_question",
                "data": {"question": "如何购买作品?"},
                "icon": "🛒"
            }
        ]
        
        # 补充到4个问题
        for q in default_questions:
            if len(questions) >= 4:
                break
            if q not in questions:
                questions.append(q)
        
        return questions[:4]
    
    def _get_default_questions(self) -> List[Dict[str, Any]]:
        """获取默认问题(当所有方法都失败时使用)"""
        return self._get_rule_based_questions()


# 全局实例
smart_questions_service = SmartQuestionsService()
