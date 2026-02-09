"""
商品推荐节点
"""
import logging
from .base import BaseNode
from ..state import ConversationState

logger = logging.getLogger(__name__)


class ProductRecommendationNode(BaseNode):
    """商品推荐节点 - 引导用户去商城"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行商品推荐 - 引导用户去商城页面"""
        
        # 客服定位调整: 不在客服中推荐商品,引导用户去商城
        state["response"] = """您好！我是售后客服，主要帮助您解决购买和使用中的问题。

**如果您想浏览和选购商品**，建议您：
1. 访问商城首页，查看所有作品
2. 使用筛选功能，按技术栈、价格、评分查找
3. 查看商品详情页，了解完整信息

**如果您需要售后帮助**，我可以协助您：
- 查询订单状态和物流信息
- 解答购买流程和支付问题
- 处理退款和售后服务
- 解决使用中遇到的问题

请问您需要什么帮助？"""
        
        # 生成快速操作按钮
        state["quick_actions"] = [
            {
                "type": "button",
                "label": "前往商城首页",
                "action": "navigate",
                "data": {"path": "/products"},
                "icon": "🏠",
                "color": "primary"
            },
            {
                "type": "button",
                "label": "查看我的订单",
                "action": "send_question",
                "data": {"question": "查看我的订单"},
                "icon": "📦"
            },
            {
                "type": "button",
                "label": "如何购买作品?",
                "action": "send_question",
                "data": {"question": "如何购买作品?"},
                "icon": "🛒"
            }
        ]
        
        return state
