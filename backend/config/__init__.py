"""
Configuration bootstrap helpers.

This package keeps the historical import path `from config import ...` while
loading the real `settings` object from `backend/config.py`.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from .loader import ConfigLoader, config_loader

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

spec = importlib.util.spec_from_file_location("app_config", backend_dir / "config.py")
app_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_config)
settings = app_config.settings


def _compact_kwargs(**kwargs: Any) -> dict[str, Any]:
    """Drop empty values before forwarding kwargs to LangChain."""
    return {key: value for key, value in kwargs.items() if value not in (None, "")}


def init_chat_model(
    temperature: float | None = None,
    max_tokens: int | None = None,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
):
    """Create the primary chat model, optionally overriding provider details."""
    from langchain.chat_models import init_chat_model as _init_chat_model

    resolved_provider = provider or settings.LLM_PROVIDER
    resolved_model = model or settings.LLM_MODEL
    resolved_api_key = api_key or settings.LLM_API_KEY
    resolved_base_url = base_url or settings.LLM_BASE_URL

    return _init_chat_model(
        model=resolved_model,
        model_provider=resolved_provider,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        max_tokens=max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS,
        **_compact_kwargs(
            api_key=resolved_api_key,
            base_url=resolved_base_url,
        ),
    )


def init_intent_model(
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
):
    """Create the dedicated intent-recognition model."""
    from langchain.chat_models import init_chat_model as _init_chat_model

    resolved_provider = provider or settings.INTENT_MODEL_PROVIDER or settings.LLM_PROVIDER
    resolved_model = model or settings.INTENT_MODEL or settings.LLM_MODEL
    resolved_api_key = api_key or settings.INTENT_API_KEY or settings.LLM_API_KEY
    resolved_base_url = base_url or settings.LLM_BASE_URL

    return _init_chat_model(
        model=resolved_model,
        model_provider=resolved_provider,
        temperature=settings.INTENT_TEMPERATURE,
        max_tokens=settings.INTENT_MAX_TOKENS,
        **_compact_kwargs(
            api_key=resolved_api_key,
            base_url=resolved_base_url,
        ),
    )


__all__ = ["ConfigLoader", "config_loader", "settings", "init_chat_model", "init_intent_model"]
