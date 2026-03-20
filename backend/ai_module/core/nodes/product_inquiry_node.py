"""
商品咨询节点
"""
import logging
from .base import BaseNode
from ..state import ConversationState

logger = logging.getLogger(__name__)


class ProductInquiryNode(BaseNode):
    """商品咨询节点 - 引导用户去商城"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行商品咨询 - 引导用户去商城页面"""
        
        # 客服定位调整: 不在客服中推荐商品,引导用户去商城
        state["response"] = """您好！关于商品浏览和选购，建议您：

1. **访问商城首页** 🏠
   - 查看所有毕业设计作品
   - 按技术栈、价格、评分筛选

2. **使用搜索功能** 🔍
   - 搜索您需要的技术栈（如Java、Vue等）
   - 查看详细的商品介绍和演示

3. **查看商品详情** 📋
   - 完整的技术栈说明
   - 功能演示视频
   - 用户评价和评分

如果您在购买过程中遇到问题，或者对已购买的商品有疑问，我随时为您服务！"""
        
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
