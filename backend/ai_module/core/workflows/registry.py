"""Workflow package registry."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional

from .base import BaseWorkflow


@dataclass
class WorkflowRegistration:
    name: str
    factory: Callable[[], BaseWorkflow]
    stream_enabled: bool = False
    workflow: Optional[BaseWorkflow] = None


class WorkflowRegistry:
    """Lazy workflow package resolver."""

    def __init__(self):
        self._workflows: Dict[str, WorkflowRegistration] = {}

    def register(self, name: str, factory: Callable[[], BaseWorkflow], *, stream_enabled: bool = False):
        self._workflows[name] = WorkflowRegistration(
            name=name,
            factory=factory,
            stream_enabled=stream_enabled,
        )

    def _resolve(self, registration: WorkflowRegistration) -> BaseWorkflow:
        if registration.workflow is None:
            registration.workflow = registration.factory()
        return registration.workflow

    def get(self, name: str) -> Optional[BaseWorkflow]:
        registration = self._workflows.get(name)
        if registration is None:
            return None
        return self._resolve(registration)

    def get_stream(self, name: str) -> Optional[BaseWorkflow]:
        registration = self._workflows.get(name)
        if registration is None or not registration.stream_enabled:
            return None
        return self._resolve(registration)
