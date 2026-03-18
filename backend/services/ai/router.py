"""旧路由器兼容层。

新的架构里由 SkillRouter 负责技能选择。
这个模块保留原有导入路径，避免现有代码和测试受影响。
"""
from __future__ import annotations

from .skill_router import SkillRouter
from .state import ConversationState


class Router(SkillRouter):
    """兼容旧调用方式的技能路由器包装层。"""

    def route_after_function_calling(self, state: ConversationState) -> str:
        return self.route(state)

    def route_by_intent(self, state: ConversationState) -> str:
        return self.route(state)
