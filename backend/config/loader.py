"""
配置加载器
负责加载和管理业务配置
"""
import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置文件目录
        """
        if config_dir is None:
            # 自动检测配置目录
            current_dir = Path(__file__).parent
            config_dir = current_dir / "businesses"
        
        self.config_dir = Path(config_dir)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """加载所有业务配置"""
        if not self.config_dir.exists():
            logger.warning(f"配置目录不存在: {self.config_dir}")
            self.config_dir.mkdir(parents=True, exist_ok=True)
            return
        
        for config_file in self.config_dir.glob("*.yaml"):
            try:
                business_id = config_file.stem
                config = self._load_config_file(config_file)
                self._configs[business_id] = config
                logger.info(f"加载配置: {business_id}")
            except Exception as e:
                logger.error(f"加载配置文件失败 {config_file}: {e}")
    
    def _load_config_file(self, config_file: Path) -> Dict[str, Any]:
        """
        加载单个配置文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            配置字典
        """
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 处理环境变量
        config = self._resolve_env_vars(config)
        
        return config
    
    def _resolve_env_vars(self, config: Any) -> Any:
        """
        解析配置中的环境变量
        
        Args:
            config: 配置对象
            
        Returns:
            解析后的配置
        """
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            # 环境变量格式: ${VAR_NAME}
            var_name = config[2:-1]
            return os.getenv(var_name, config)
        else:
            return config
    
    def get_config(self, business_id: str) -> Optional[Dict[str, Any]]:
        """
        获取业务配置
        
        Args:
            business_id: 业务标识
            
        Returns:
            业务配置，如果不存在返回None
        """
        return self._configs.get(business_id)
    
    def reload_config(self, business_id: str):
        """
        重新加载指定业务的配置
        
        Args:
            business_id: 业务标识
        """
        config_file = self.config_dir / f"{business_id}.yaml"
        if config_file.exists():
            try:
                config = self._load_config_file(config_file)
                self._configs[business_id] = config
                logger.info(f"重新加载配置: {business_id}")
            except Exception as e:
                logger.error(f"重新加载配置失败 {business_id}: {e}")
        else:
            logger.warning(f"配置文件不存在: {config_file}")
    
    def list_businesses(self) -> list:
        """
        列出所有已配置的业务
        
        Returns:
            业务ID列表
        """
        return list(self._configs.keys())
    
    def has_business(self, business_id: str) -> bool:
        """
        检查业务是否已配置
        
        Args:
            business_id: 业务标识
            
        Returns:
            是否存在
        """
        return business_id in self._configs
    
    def get_adapter_class(self, business_id: str) -> Optional[str]:
        """
        获取业务的适配器类名
        
        Args:
            business_id: 业务标识
            
        Returns:
            适配器类名，如果不存在返回None
        """
        config = self.get_config(business_id)
        if config:
            return config.get("adapter", {}).get("class")
        return None
    
    def get_plugins_config(self, business_id: str) -> list:
        """
        获取业务的插件配置
        
        Args:
            business_id: 业务标识
            
        Returns:
            插件配置列表
        """
        config = self.get_config(business_id)
        if config:
            return config.get("plugins", [])
        return []


# 全局配置加载器实例
config_loader = ConfigLoader()
