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

def init_chat_model(temperature: float = None, max_tokens: int = None):
    """统一初始化LLM"""
    from langchain.chat_models import init_chat_model as _init_chat_model
    return _init_chat_model(
        model=settings.DEEPSEEK_MODEL,
        model_provider="deepseek",
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        max_tokens=max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS,
        api_key=settings.DEEPSEEK_API_KEY,
    )


def init_intent_model():
    """初始化意图识别专用LLM（低temperature、少token、可独立配置模型）"""
    from langchain.chat_models import init_chat_model as _init_chat_model
    
    model = settings.INTENT_MODEL or settings.DEEPSEEK_MODEL
    provider = settings.INTENT_MODEL_PROVIDER or "deepseek"
    api_key = settings.INTENT_API_KEY or settings.DEEPSEEK_API_KEY
    
    return _init_chat_model(
        model=model,
        model_provider=provider,
        temperature=settings.INTENT_TEMPERATURE,
        max_tokens=settings.INTENT_MAX_TOKENS,
        api_key=api_key,
    )

__all__ = ["ConfigLoader", "config_loader", "settings", "init_chat_model", "init_intent_model"]
