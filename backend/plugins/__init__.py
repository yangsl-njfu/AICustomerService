"""
插件系统模块
提供插件基类和插件管理器
"""
from .base import AIPlugin
from .manager import PluginManager, plugin_manager

__all__ = ["AIPlugin", "PluginManager", "plugin_manager"]
