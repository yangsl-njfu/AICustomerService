"""工作流路由处理器注册表。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class HandlerRegistration:
    name: str
    node: Any
    stream_enabled: bool = False


class HandlerRegistry:
    """保存工作流内核使用的路由处理器。"""

    def __init__(self):
        self._handlers: Dict[str, HandlerRegistration] = {}

    def register(self, name: str, node: Any, *, stream_enabled: bool = False):
        self._handlers[name] = HandlerRegistration(
            name=name,
            node=node,
            stream_enabled=stream_enabled,
        )

    def get(self, name: str, default: Optional[Any] = None):
        registration = self._handlers.get(name)
        if registration is None:
            return default
        return registration.node

    def get_stream(self, name: str, default: Optional[Any] = None):
        registration = self._handlers.get(name)
        if registration is None:
            return default
        if registration.stream_enabled and hasattr(registration.node, "execute_stream"):
            return registration.node
        return default

    def has(self, name: str) -> bool:
        return name in self._handlers
