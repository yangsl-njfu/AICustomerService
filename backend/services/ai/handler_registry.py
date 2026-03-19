"""工作流路由处理器注册表。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass
class HandlerRegistration:
    name: str
    node: Any = None
    factory: Optional[Callable[[], Any]] = None
    stream_enabled: bool = False


class HandlerRegistry:
    """保存工作流内核使用的路由处理器。"""

    def __init__(self):
        self._handlers: Dict[str, HandlerRegistration] = {}

    def register(
        self,
        name: str,
        node: Any = None,
        *,
        factory: Optional[Callable[[], Any]] = None,
        stream_enabled: bool = False,
    ):
        if node is None and factory is None:
            raise ValueError("HandlerRegistry.register requires either node or factory")
        self._handlers[name] = HandlerRegistration(
            name=name,
            node=node,
            factory=factory,
            stream_enabled=stream_enabled,
        )

    def _resolve(self, registration: HandlerRegistration):
        if registration.node is None and registration.factory is not None:
            registration.node = registration.factory()
        return registration.node

    def get(self, name: str, default: Optional[Any] = None):
        registration = self._handlers.get(name)
        if registration is None:
            return default
        return self._resolve(registration)

    def get_stream(self, name: str, default: Optional[Any] = None):
        registration = self._handlers.get(name)
        if registration is None:
            return default
        node = self._resolve(registration)
        if registration.stream_enabled and hasattr(node, "execute_stream"):
            return node
        return default

    def has(self, name: str) -> bool:
        return name in self._handlers
