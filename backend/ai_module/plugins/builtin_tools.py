"""Compatibility facade for legacy built-in plugin imports."""

from ..infrastructure.plugins.builtin_tools import LangChainToolPlugin, register_builtin_tool_plugins

__all__ = ["LangChainToolPlugin", "register_builtin_tool_plugins"]
