"""
插件管理器
负责插件的注册、加载和执行
"""
from typing import Dict, List, Any, Optional
from .base import AIPlugin
import logging

logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        """初始化插件管理器"""
        self.plugins: Dict[str, AIPlugin] = {}
        self._adapter = None
    
    def set_adapter(self, adapter: Any):
        """
        设置业务适配器
        
        Args:
            adapter: 业务适配器实例
        """
        self._adapter = adapter
        # 更新所有已注册插件的适配器
        for plugin in self.plugins.values():
            plugin.adapter = adapter
    
    def register(self, plugin: AIPlugin):
        """
        注册插件
        
        Args:
            plugin: 插件实例
        """
        if plugin.name in self.plugins:
            logger.warning(f"插件 {plugin.name} 已存在，将被覆盖")
        
        # 设置适配器
        if self._adapter:
            plugin.adapter = self._adapter
        
        self.plugins[plugin.name] = plugin
        logger.info(f"插件 {plugin.name} 注册成功")
    
    def unregister(self, plugin_name: str):
        """
        注销插件
        
        Args:
            plugin_name: 插件名称
        """
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            logger.info(f"插件 {plugin_name} 已注销")
    
    async def execute(self, plugin_name: str, **kwargs) -> Any:
        """
        执行插件
        
        Args:
            plugin_name: 插件名称
            **kwargs: 插件参数
            
        Returns:
            插件执行结果
            
        Raises:
            ValueError: 插件不存在
        """
        if plugin_name not in self.plugins:
            raise ValueError(f"插件 {plugin_name} 不存在")
        
        plugin = self.plugins[plugin_name]
        logger.info(f"执行插件: {plugin_name}")
        
        try:
            result = await plugin.execute(**kwargs)
            logger.info(f"插件 {plugin_name} 执行成功")
            return result
        except Exception as e:
            logger.error(f"插件 {plugin_name} 执行失败: {e}")
            raise
    
    def get_plugin(self, plugin_name: str) -> Optional[AIPlugin]:
        """
        获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件实例，如果不存在返回None
        """
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[Dict]:
        """
        列出所有插件
        
        Returns:
            插件元数据列表
        """
        return [plugin.get_metadata() for plugin in self.plugins.values()]
    
    def get_plugin_schemas(self) -> Dict[str, Dict]:
        """
        获取所有插件的schema（用于Function Calling）
        
        Returns:
            插件名称到schema的映射
        """
        return {
            plugin.name: plugin.get_schema()
            for plugin in self.plugins.values()
        }
    
    def has_plugin(self, plugin_name: str) -> bool:
        """
        检查插件是否存在
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否存在
        """
        return plugin_name in self.plugins


# 全局插件管理器实例
plugin_manager = PluginManager()
