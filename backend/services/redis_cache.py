"""
Redis缓存服务（使用内存缓存作为替代，无需安装Redis）
"""
import json
from typing import Optional, Dict, List, Any
from datetime import datetime


class MemoryCache:
    """内存缓存服务类（替代Redis）"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}

    async def connect(self):
        """连接（内存缓存无需实际连接）"""
        print("✅ 内存缓存已初始化")

    async def disconnect(self):
        """断开连接"""
        self._cache.clear()

    async def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话上下文"""
        key = f"session:{session_id}:context"
        data = self._cache.get(key)

        if not data:
            return None

        return {
            "history": data.get("history", []),
            "user_profile": data.get("user_profile", {}),
            "last_intent": data.get("last_intent"),
            "intent_history": data.get("intent_history", []),
            "conversation_summary": data.get("conversation_summary", ""),
            "updated_at": data.get("updated_at")
        }

    async def update_context(
        self,
        session_id: str,
        history: Optional[List[Dict]] = None,
        user_profile: Optional[Dict] = None,
        last_intent: Optional[str] = None,
        intent_history: Optional[List[Dict]] = None,
        conversation_summary: Optional[str] = None
    ):
        """更新会话上下文"""
        key = f"session:{session_id}:context"
        existing = self._cache.get(key, {})

        if history is not None:
            existing["history"] = history
        if user_profile is not None:
            existing["user_profile"] = user_profile
        if last_intent is not None:
            existing["last_intent"] = last_intent
        if intent_history is not None:
            existing["intent_history"] = intent_history
        if conversation_summary is not None:
            existing["conversation_summary"] = conversation_summary

        existing["updated_at"] = datetime.now().isoformat()
        self._cache[key] = existing

    async def clear_context(self, session_id: str):
        """清除会话上下文"""
        key = f"session:{session_id}:context"
        if key in self._cache:
            del self._cache[key]

    async def add_message_to_context(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str
    ):
        """添加消息到上下文"""
        key = f"session:{session_id}:context"
        existing = self._cache.get(key, {})

        if "history" not in existing:
            existing["history"] = []

        existing["history"].append({
            "user": user_message,
            "assistant": assistant_message,
            "timestamp": datetime.now().isoformat()
        })

        # 只保留最近20轮对话
        existing["history"] = existing["history"][-20:]
        existing["updated_at"] = datetime.now().isoformat()
        self._cache[key] = existing

    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        return self._cache.get(key)

    async def set(self, key: str, value: str, expire: Optional[int] = None):
        """设置缓存值"""
        self._cache[key] = value

    async def delete(self, key: str):
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]


# 全局缓存实例
redis_cache = MemoryCache()
