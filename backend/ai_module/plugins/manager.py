"""Compatibility facade for legacy plugin manager imports."""

from ..infrastructure.plugins.manager import PluginManager, plugin_manager

__all__ = ["PluginManager", "plugin_manager"]
