"""
插件系统基类
定义插件接口和插件管理器
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AIPlugin(ABC):
    """AI插件基类 - 所有插件必须实现此接口"""
    
    def __init__(self, adapter: Optional[Any] = None):
        """
        初始化插件
        
        Args:
            adapter: 业务适配器实例
        """
        self.adapter = adapter
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称（唯一标识）"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        执行插件功能
        
        Args:
            **kwargs: 插件参数
            
        Returns:
            执行结果
        """
        pass
    
    def get_schema(self) -> Dict:
        """
        返回插件的参数schema（用于Function Calling）
        
        Returns:
            JSON Schema格式的参数定义
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取插件元数据
        
        Returns:
            插件元数据
        """
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.get_schema()
        }
