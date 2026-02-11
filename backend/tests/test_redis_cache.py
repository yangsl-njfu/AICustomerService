"""
Unit tests for redis_cache.py — verifying intent_history and conversation_summary
support in get_context and update_context methods.
"""
import sys
import os
import importlib.util

import pytest
import pytest_asyncio

# Import MemoryCache directly from the file to avoid the heavy services/__init__.py chain
_spec = importlib.util.spec_from_file_location(
    "redis_cache",
    os.path.join(os.path.dirname(__file__), "..", "services", "redis_cache.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
MemoryCache = _mod.MemoryCache


@pytest_asyncio.fixture
async def cache():
    """Provide a fresh MemoryCache instance for each test."""
    c = MemoryCache()
    await c.connect()
    yield c
    await c.disconnect()


# ── get_context defaults ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_context_returns_none_for_unknown_session(cache: MemoryCache):
    result = await cache.get_context("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_context_returns_default_new_fields(cache: MemoryCache):
    """Existing contexts without intent_history / conversation_summary
    should return [] and '' respectively (backward compatibility)."""
    # Manually seed a legacy context without the new fields
    cache._cache["session:legacy:context"] = {
        "history": [{"user": "hi", "assistant": "hello", "timestamp": "t"}],
        "user_profile": {"name": "Alice"},
        "last_intent": "问答",
        "updated_at": "2024-01-01T00:00:00",
    }

    ctx = await cache.get_context("legacy")
    assert ctx is not None
    assert ctx["intent_history"] == []
    assert ctx["conversation_summary"] == ""
    # Original fields still present
    assert len(ctx["history"]) == 1
    assert ctx["last_intent"] == "问答"


@pytest.mark.asyncio
async def test_get_context_returns_stored_new_fields(cache: MemoryCache):
    """When intent_history and conversation_summary are stored, get_context returns them."""
    intent_history = [
        {"intent": "商品咨询", "confidence": 0.95, "turn": 1, "timestamp": "t1"},
    ]
    cache._cache["session:s1:context"] = {
        "history": [],
        "user_profile": {},
        "last_intent": "商品咨询",
        "intent_history": intent_history,
        "conversation_summary": "User asked about products.",
        "updated_at": "2024-01-01T00:00:00",
    }

    ctx = await cache.get_context("s1")
    assert ctx["intent_history"] == intent_history
    assert ctx["conversation_summary"] == "User asked about products."


# ── update_context with new fields ───────────────────────────────────

@pytest.mark.asyncio
async def test_update_context_persists_intent_history(cache: MemoryCache):
    intent_history = [
        {"intent": "订单查询", "confidence": 0.8, "turn": 1, "timestamp": "t1"},
        {"intent": "商品咨询", "confidence": 0.9, "turn": 2, "timestamp": "t2"},
    ]
    await cache.update_context("s2", intent_history=intent_history)

    ctx = await cache.get_context("s2")
    assert ctx["intent_history"] == intent_history


@pytest.mark.asyncio
async def test_update_context_persists_conversation_summary(cache: MemoryCache):
    summary = "The user inquired about order ORD123 and product availability."
    await cache.update_context("s3", conversation_summary=summary)

    ctx = await cache.get_context("s3")
    assert ctx["conversation_summary"] == summary


@pytest.mark.asyncio
async def test_update_context_does_not_overwrite_unset_fields(cache: MemoryCache):
    """Calling update_context with only one new field should not erase the other."""
    await cache.update_context(
        "s4",
        intent_history=[{"intent": "问答", "confidence": 0.7, "turn": 1, "timestamp": "t"}],
        conversation_summary="initial summary",
    )
    # Now update only the summary
    await cache.update_context("s4", conversation_summary="updated summary")

    ctx = await cache.get_context("s4")
    assert len(ctx["intent_history"]) == 1  # unchanged
    assert ctx["conversation_summary"] == "updated summary"


@pytest.mark.asyncio
async def test_update_context_preserves_original_fields(cache: MemoryCache):
    """Updating new fields should not affect existing original fields."""
    await cache.update_context("s5", last_intent="问答", user_profile={"name": "Bob"})
    await cache.update_context(
        "s5",
        intent_history=[{"intent": "问答", "confidence": 0.85, "turn": 1, "timestamp": "t"}],
    )

    ctx = await cache.get_context("s5")
    assert ctx["last_intent"] == "问答"
    assert ctx["user_profile"] == {"name": "Bob"}
    assert len(ctx["intent_history"]) == 1


@pytest.mark.asyncio
async def test_update_context_all_fields_together(cache: MemoryCache):
    """All fields (old + new) can be set in a single call."""
    history = [{"user": "hi", "assistant": "hello", "timestamp": "t"}]
    intent_history = [{"intent": "商品推荐", "confidence": 0.92, "turn": 1, "timestamp": "t"}]
    summary = "Comprehensive summary."

    await cache.update_context(
        "s6",
        history=history,
        user_profile={"vip": True},
        last_intent="商品推荐",
        intent_history=intent_history,
        conversation_summary=summary,
    )

    ctx = await cache.get_context("s6")
    assert ctx["history"] == history
    assert ctx["user_profile"] == {"vip": True}
    assert ctx["last_intent"] == "商品推荐"
    assert ctx["intent_history"] == intent_history
    assert ctx["conversation_summary"] == summary
    assert ctx["updated_at"] is not None
