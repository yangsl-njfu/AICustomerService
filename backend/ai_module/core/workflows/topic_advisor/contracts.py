"""Topic advisor workflow contracts."""
from __future__ import annotations

from enum import Enum


class TopicAdvisorMode(str, Enum):
    DIRECT_RECOMMEND = "direct_recommend"
    REFINE_PREFERENCES = "refine_preferences"
