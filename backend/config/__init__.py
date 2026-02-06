"""
配置模块
提供配置加载和管理功能
"""
from .loader import ConfigLoader, config_loader

# 从上级目录的config.py导入settings
import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 导入settings (从backend/config.py)
import importlib.util
spec = importlib.util.spec_from_file_location("app_config", backend_dir / "config.py")
app_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_config)
settings = app_config.settings

__all__ = ["ConfigLoader", "config_loader", "settings"]
