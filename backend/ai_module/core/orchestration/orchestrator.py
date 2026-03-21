"""
AI 工作流总编排入口（薄门面）。

说明：
- 组装运行时、模型、路由与注册表
- 其余职责拆分到 ``orchestrator_parts`` 子模块
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from config import init_chat_model, init_intent_model

from .handler_registry import HandlerRegistry
from ..nodes import (
    ContextNode,
    ConversationControlNode,
    DialogueStateNode,
    FunctionCallingNode,
    MessageEntryNode,
    PolicyNode,
    ResponsePlannerNode,
    SaveContextNode,
)
from .orchestrator_parts import (
    WorkflowBootstrapMixin,
    WorkflowEntrypointsMixin,
    WorkflowExecuteMixin,
    WorkflowPrepareMixin,
    WorkflowStateMixin,
)
from .router import Router
from ..runtime import runtime_factory
from ..workflows import WorkflowRegistry

if TYPE_CHECKING:
    from ...application.ports import RuntimePort


class AIWorkflow(
    WorkflowBootstrapMixin,
    WorkflowStateMixin,
    WorkflowPrepareMixin,
    WorkflowExecuteMixin,
    WorkflowEntrypointsMixin,
):
    """单业务运行时下的 AI 工作流。"""

    def __init__(self, runtime: "RuntimePort | None" = None):
        self.runtime = runtime or runtime_factory.get_runtime()
        self.llm = self.runtime.get_chat_model("chat") if self.runtime else init_chat_model()
        self.intent_llm = self.runtime.get_chat_model("intent") if self.runtime else init_intent_model()
        self.router = Router(runtime=self.runtime)

        # Core pipeline nodes
        self.context_node = ContextNode()
        self.message_entry_node = MessageEntryNode(self.intent_llm, runtime=self.runtime)
        self.response_planner_node = ResponsePlannerNode(runtime=self.runtime)
        self.policy_node = PolicyNode(runtime=self.runtime)
        self.conversation_control_node = ConversationControlNode(self.llm, runtime=self.runtime)
        self.dialogue_state_node = DialogueStateNode()
        self.function_calling_node = FunctionCallingNode(self.llm, runtime=self.runtime)
        self.save_context_node = SaveContextNode(self.llm)

        # Lazy registries
        self._lazy_nodes: Dict[str, Any] = {}
        self._lazy_workflows: Dict[str, Any] = {}
        self.handlers = HandlerRegistry()
        self.workflows = WorkflowRegistry()

        self._register_builtin_handlers()
        self._register_builtin_workflows()
        self.graph = None


class _DefaultWorkflowProxy:
    """兼容旧导入路径的惰性代理。"""

    def __getattr__(self, item: str):
        return getattr(runtime_factory.get_workflow(), item)


ai_workflow = _DefaultWorkflowProxy()
