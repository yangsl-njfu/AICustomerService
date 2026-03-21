"""Base class for topic advisor workflow nodes."""
from __future__ import annotations

from ..common.base import BaseNode
from ...workflows.topic_advisor.service import TopicAdvisorService


class TopicAdvisorStepNode(BaseNode):
    """Shared helper for topic advisor workflow nodes."""

    def __init__(self, service: TopicAdvisorService):
        super().__init__(llm=service.llm, runtime=service.runtime)
        self.service = service
