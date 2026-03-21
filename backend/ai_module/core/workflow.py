"""Compatibility facade for legacy ``ai_module.core.workflow`` imports."""

from .orchestration import (
    AIWorkflow,
    HandlerRegistration,
    HandlerRegistry,
    Router,
    SkillRouter,
    ai_workflow,
)

__all__ = [
    "AIWorkflow",
    "ai_workflow",
    "Router",
    "SkillRouter",
    "HandlerRegistry",
    "HandlerRegistration",
]
