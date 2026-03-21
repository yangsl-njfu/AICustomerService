"""Base class for QA workflow nodes."""
from __future__ import annotations

from ..common.base import BaseNode
from ...workflows.qa_flow.service import QAFlowService


class QAFlowStepNode(BaseNode):
    """Shared helper for QA workflow nodes."""

    def __init__(self, service: QAFlowService):
        super().__init__(llm=service.llm, runtime=service.runtime)
        self.service = service
