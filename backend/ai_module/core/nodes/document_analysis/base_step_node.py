"""Base class for document analysis workflow nodes."""
from __future__ import annotations

from ..common.base import BaseNode
from ...workflows.document_analysis.service import DocumentAnalysisService


class DocumentAnalysisStepNode(BaseNode):
    """Shared helper for document analysis workflow nodes."""

    def __init__(self, service: DocumentAnalysisService):
        super().__init__(llm=service.llm, runtime=service.runtime)
        self.service = service
