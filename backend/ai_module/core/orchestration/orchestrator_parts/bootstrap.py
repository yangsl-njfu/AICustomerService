"""Bootstrap mixin for node/workflow factories and registry wiring."""
from __future__ import annotations

from importlib import import_module
from typing import Any


class WorkflowBootstrapMixin:
    """Factory and registration helpers for AIWorkflow."""

    def _register_builtin_handlers(self) -> None:
        self.handlers.register("qa_flow", factory=self._get_qa_node, stream_enabled=True)
        self.handlers.register("ticket_flow", factory=self._get_ticket_node)
        self.handlers.register("document_analysis", factory=self._get_document_node, stream_enabled=True)
        self.handlers.register("clarify", factory=self._get_clarify_node, stream_enabled=True)
        self.handlers.register("domain_scope_guard", factory=self._get_domain_scope_guard_node)
        self.handlers.register("cart_inquiry", factory=self._get_cart_inquiry_node)
        self.handlers.register("unsupported_capability", factory=self._get_unsupported_capability_node)
        self.handlers.register("product_inquiry", factory=self._get_product_inquiry_node)
        self.handlers.register("order_query", factory=self._get_order_query_node)
        self.handlers.register("purchase_guide", factory=self._get_purchase_guide_node, stream_enabled=True)
        self.handlers.register("aftersales_flow", factory=self._get_aftersales_flow_node)
        self.handlers.register("topic_advisor", factory=self._get_topic_advisor_node, stream_enabled=True)

    def _register_builtin_workflows(self) -> None:
        self.workflows.register("purchase_flow", factory=self._get_purchase_flow_workflow)
        self.workflows.register("aftersales_flow", factory=self._get_aftersales_flow_workflow)
        self.workflows.register(
            "topic_advisor",
            factory=self._get_topic_advisor_workflow,
            stream_enabled=True,
        )

    def _get_or_create_node(self, key: str, factory):
        node = self._lazy_nodes.get(key)
        if node is None:
            node = factory()
            self._lazy_nodes[key] = node
        return node

    def _get_or_create_workflow(self, key: str, factory):
        workflow = self._lazy_workflows.get(key)
        if workflow is None:
            workflow = factory()
            self._lazy_workflows[key] = workflow
        return workflow

    def _instantiate_node(self, key: str, module_path: str, class_name: str, *args, **kwargs):
        return self._get_or_create_node(
            key,
            lambda: getattr(import_module(module_path), class_name)(*args, **kwargs),
        )

    def _instantiate_workflow(self, key: str, module_path: str, class_name: str, *args, **kwargs):
        return self._get_or_create_workflow(
            key,
            lambda: getattr(import_module(module_path), class_name)(*args, **kwargs),
        )

    def _get_qa_node(self):
        return self._instantiate_node(
            "qa_flow",
            "ai_module.core.nodes.skills.qa_node",
            "QANode",
            self.llm,
            runtime=self.runtime,
        )

    def _get_document_node(self):
        return self._instantiate_node(
            "document_analysis",
            "ai_module.core.nodes.skills.document_node",
            "DocumentNode",
            self.llm,
        )

    def _get_ticket_node(self):
        return self._instantiate_node(
            "ticket_flow",
            "ai_module.core.nodes.skills.ticket_node",
            "TicketNode",
            self.llm,
        )

    def _get_clarify_node(self):
        return self._instantiate_node(
            "clarify",
            "ai_module.core.nodes.skills.clarify_node",
            "ClarifyNode",
            self.llm,
        )

    def _get_cart_inquiry_node(self):
        return self._instantiate_node(
            "cart_inquiry",
            "ai_module.core.nodes.skills.cart_inquiry_node",
            "CartInquiryNode",
            self.llm,
        )

    def _get_domain_scope_guard_node(self):
        return self._instantiate_node(
            "domain_scope_guard",
            "ai_module.core.nodes.skills.domain_scope_guard_node",
            "DomainScopeGuardNode",
            self.llm,
            runtime=self.runtime,
        )

    def _get_unsupported_capability_node(self):
        return self._instantiate_node(
            "unsupported_capability",
            "ai_module.core.nodes.skills.unsupported_capability_node",
            "UnsupportedCapabilityNode",
            self.llm,
            runtime=self.runtime,
        )

    def _get_product_inquiry_node(self):
        return self._instantiate_node(
            "product_inquiry",
            "ai_module.core.nodes.skills.product_inquiry_node",
            "ProductInquiryNode",
            self.llm,
        )

    def _get_order_query_node(self):
        return self._instantiate_node(
            "order_query",
            "ai_module.core.nodes.skills.order_query_node",
            "OrderQueryNode",
            self.llm,
        )

    def _get_purchase_guide_node(self):
        return self._instantiate_node(
            "purchase_guide",
            "ai_module.core.nodes.skills.purchase_guide_node",
            "PurchaseGuideNode",
            self.llm,
        )

    def _get_purchase_flow_node(self):
        return self._instantiate_node(
            "purchase_flow",
            "ai_module.core.nodes.skills.purchase_flow_node",
            "PurchaseFlowNode",
        )

    def _get_aftersales_flow_node(self):
        return self._instantiate_node(
            "aftersales_flow",
            "ai_module.core.nodes.skills.aftersales_flow_node",
            "AftersalesFlowNode",
        )

    def _get_topic_advisor_node(self):
        return self._instantiate_node(
            "topic_advisor",
            "ai_module.core.nodes.skills.topic_advisor_node",
            "TopicAdvisorNode",
            self.llm,
            runtime=self.runtime,
        )

    def _get_purchase_flow_workflow(self):
        return self._instantiate_workflow(
            "purchase_flow_workflow",
            "ai_module.core.workflows.purchase_flow.workflow",
            "PurchaseFlowWorkflow",
        )

    def _get_aftersales_flow_workflow(self):
        return self._instantiate_workflow(
            "aftersales_flow_workflow",
            "ai_module.core.workflows.aftersales_flow.workflow",
            "AftersalesFlowWorkflow",
        )

    def _get_topic_advisor_workflow(self):
        return self._instantiate_workflow(
            "topic_advisor_workflow",
            "ai_module.core.workflows.topic_advisor.workflow",
            "TopicAdvisorWorkflow",
            self.llm,
            runtime=self.runtime,
        )
