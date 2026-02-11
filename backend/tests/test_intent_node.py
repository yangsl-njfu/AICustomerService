"""
Unit tests for intent_node.py — verifying intent history prompt formatting,
fallback logic, and intent history append behavior.
"""
import sys
import os
import types
import importlib.util
from unittest.mock import AsyncMock, MagicMock

import pytest

# ── Bootstrap: set up the module hierarchy so intent_node's relative imports work ──

_backend_dir = os.path.join(os.path.dirname(__file__), "..")

# Create package stubs so relative imports resolve
for pkg in [
    "backend",
    "backend.services",
    "backend.services.ai",
    "backend.services.ai.nodes",
]:
    if pkg not in sys.modules:
        sys.modules[pkg] = types.ModuleType(pkg)

# Load state.py
_state_path = os.path.join(_backend_dir, "services", "ai", "state.py")
_state_spec = importlib.util.spec_from_file_location("backend.services.ai.state", _state_path)
_state_mod = importlib.util.module_from_spec(_state_spec)
sys.modules["backend.services.ai.state"] = _state_mod
_state_spec.loader.exec_module(_state_mod)

# Load base.py
_base_path = os.path.join(_backend_dir, "services", "ai", "nodes", "base.py")
_base_spec = importlib.util.spec_from_file_location("backend.services.ai.nodes.base", _base_path)
_base_mod = importlib.util.module_from_spec(_base_spec)
sys.modules["backend.services.ai.nodes.base"] = _base_mod
_base_spec.loader.exec_module(_base_mod)

# Load config.py
_config_path = os.path.join(_backend_dir, "config.py")
_config_spec = importlib.util.spec_from_file_location("backend.config", _config_path)
_config_mod = importlib.util.module_from_spec(_config_spec)
sys.modules["backend.config"] = _config_mod
_config_spec.loader.exec_module(_config_mod)

# Load intent_node.py
_intent_path = os.path.join(_backend_dir, "services", "ai", "nodes", "intent_node.py")
_intent_spec = importlib.util.spec_from_file_location(
    "backend.services.ai.nodes.intent_node", _intent_path,
    submodule_search_locations=[],
)
_intent_mod = importlib.util.module_from_spec(_intent_spec)
_intent_mod.__package__ = "backend.services.ai.nodes"
sys.modules["backend.services.ai.nodes.intent_node"] = _intent_mod
_intent_spec.loader.exec_module(_intent_mod)

_format_intent_history = _intent_mod._format_intent_history
_find_fallback_intent = _intent_mod._find_fallback_intent
IntentRecognitionNode = _intent_mod.IntentRecognitionNode
VALID_INTENTS = _intent_mod.VALID_INTENTS


# ── _format_intent_history tests ─────────────────────────────────────

class TestFormatIntentHistory:
    def test_empty_history_returns_placeholder(self):
        result = _format_intent_history([], max_entries=5)
        assert result == "（无历史记录）"

    def test_single_entry(self):
        history = [{"intent": "商品咨询", "confidence": 0.9, "turn": 1}]
        result = _format_intent_history(history, max_entries=5)
        assert "第1轮" in result
        assert "商品咨询" in result
        assert "0.9" in result

    def test_respects_max_entries_limit(self):
        history = [
            {"intent": "问答", "confidence": 0.8, "turn": i}
            for i in range(1, 11)
        ]
        result = _format_intent_history(history, max_entries=3)
        lines = result.strip().split("\n")
        assert len(lines) == 3
        # Should contain the last 3 entries (turns 8, 9, 10)
        assert "第8轮" in lines[0]
        assert "第9轮" in lines[1]
        assert "第10轮" in lines[2]

    def test_fewer_entries_than_max(self):
        history = [
            {"intent": "订单查询", "confidence": 0.85, "turn": 1},
            {"intent": "商品推荐", "confidence": 0.9, "turn": 2},
        ]
        result = _format_intent_history(history, max_entries=5)
        lines = result.strip().split("\n")
        assert len(lines) == 2

    def test_missing_fields_use_defaults(self):
        history = [{"intent": "问答"}]  # missing confidence and turn
        result = _format_intent_history(history, max_entries=5)
        assert "第0轮" in result
        assert "0.0" in result


# ── _find_fallback_intent tests ──────────────────────────────────────

class TestFindFallbackIntent:
    def test_empty_history_returns_none(self):
        assert _find_fallback_intent([], threshold=0.6) is None

    def test_all_below_threshold_returns_none(self):
        history = [
            {"intent": "问答", "confidence": 0.3, "turn": 1},
            {"intent": "商品咨询", "confidence": 0.5, "turn": 2},
        ]
        assert _find_fallback_intent(history, threshold=0.6) is None

    def test_returns_most_recent_above_threshold(self):
        history = [
            {"intent": "商品咨询", "confidence": 0.9, "turn": 1},
            {"intent": "订单查询", "confidence": 0.8, "turn": 2},
            {"intent": "问答", "confidence": 0.3, "turn": 3},
        ]
        result = _find_fallback_intent(history, threshold=0.6)
        assert result == "订单查询"  # most recent with confidence >= 0.6

    def test_exact_threshold_is_included(self):
        history = [
            {"intent": "工单", "confidence": 0.6, "turn": 1},
        ]
        result = _find_fallback_intent(history, threshold=0.6)
        assert result == "工单"

    def test_single_high_confidence_entry(self):
        history = [
            {"intent": "购买指导", "confidence": 0.95, "turn": 1},
        ]
        result = _find_fallback_intent(history, threshold=0.6)
        assert result == "购买指导"


# ── _append_intent_history tests ─────────────────────────────────────

class TestAppendIntentHistory:
    def setup_method(self):
        self.node = IntentRecognitionNode(llm=None)

    def test_append_to_empty_history(self):
        state = {}
        self.node._append_intent_history(state, [], "商品咨询", 0.9)
        assert len(state["intent_history"]) == 1
        entry = state["intent_history"][0]
        assert entry["intent"] == "商品咨询"
        assert entry["confidence"] == 0.9
        assert entry["turn"] == 1
        assert "timestamp" in entry

    def test_append_increments_turn(self):
        existing = [
            {"intent": "问答", "confidence": 0.8, "turn": 3, "timestamp": "t"},
        ]
        state = {}
        self.node._append_intent_history(state, existing, "订单查询", 0.85)
        assert len(state["intent_history"]) == 2
        assert state["intent_history"][-1]["turn"] == 4

    def test_does_not_mutate_original_list(self):
        original = [
            {"intent": "问答", "confidence": 0.8, "turn": 1, "timestamp": "t"},
        ]
        original_len = len(original)
        state = {}
        self.node._append_intent_history(state, original, "工单", 0.7)
        assert len(original) == original_len  # original unchanged
        assert len(state["intent_history"]) == original_len + 1


# ── IntentRecognitionNode.execute integration tests ──────────────────

class TestIntentRecognitionNodeExecute:
    def setup_method(self):
        # Clear the class-level cache before each test
        IntentRecognitionNode._intent_cache.clear()

    def _make_state(self, message="你好", intent_history=None, attachments=None):
        return {
            "user_message": message,
            "user_id": "test_user",
            "session_id": "test_session",
            "attachments": attachments,
            "conversation_history": [],
            "user_profile": {},
            "intent": None,
            "confidence": None,
            "intent_history": intent_history,
        }

    def _make_mock_llm(self, response_text="问答"):
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = response_text
        mock_llm.ainvoke.return_value = mock_response
        return mock_llm

    @pytest.mark.asyncio
    async def test_execute_appends_to_empty_intent_history(self):
        mock_llm = self._make_mock_llm("商品推荐")
        node = IntentRecognitionNode(llm=mock_llm)
        state = self._make_state(message="推荐几个项目", intent_history=[])

        result = await node.execute(state)

        assert result["intent"] == "商品推荐"
        assert len(result["intent_history"]) == 1
        assert result["intent_history"][0]["intent"] == "商品推荐"
        assert result["intent_history"][0]["turn"] == 1

    @pytest.mark.asyncio
    async def test_execute_appends_to_existing_intent_history(self):
        mock_llm = self._make_mock_llm("订单查询")
        node = IntentRecognitionNode(llm=mock_llm)
        existing_history = [
            {"intent": "商品咨询", "confidence": 0.9, "turn": 1, "timestamp": "t1"},
        ]
        state = self._make_state(
            message="我的订单到哪了",
            intent_history=existing_history,
        )

        result = await node.execute(state)

        assert result["intent"] == "订单查询"
        assert len(result["intent_history"]) == 2
        assert result["intent_history"][-1]["intent"] == "订单查询"
        assert result["intent_history"][-1]["turn"] == 2

    @pytest.mark.asyncio
    async def test_execute_uses_history_prompt_when_history_exists(self):
        mock_llm = self._make_mock_llm("商品咨询")
        node = IntentRecognitionNode(llm=mock_llm)
        existing_history = [
            {"intent": "商品推荐", "confidence": 0.9, "turn": 1, "timestamp": "t1"},
        ]
        state = self._make_state(
            message="这个项目多少钱",
            intent_history=existing_history,
        )

        await node.execute(state)

        # Verify LLM was called with messages that include intent history
        call_args = mock_llm.ainvoke.call_args[0][0]
        system_msg = call_args[0].content
        assert "意图历史" in system_msg
        assert "商品推荐" in system_msg

    @pytest.mark.asyncio
    async def test_execute_uses_basic_prompt_when_no_history(self):
        mock_llm = self._make_mock_llm("问答")
        node = IntentRecognitionNode(llm=mock_llm)
        state = self._make_state(message="你好", intent_history=[])

        await node.execute(state)

        call_args = mock_llm.ainvoke.call_args[0][0]
        system_msg = call_args[0].content
        assert "意图历史" not in system_msg

    @pytest.mark.asyncio
    async def test_attachment_shortcut_appends_to_history(self):
        node = IntentRecognitionNode(llm=None)
        state = self._make_state(
            message="分析一下",
            intent_history=[],
            attachments=[{"name": "file.pdf"}],
        )

        result = await node.execute(state)

        assert result["intent"] == "文档分析"
        assert len(result["intent_history"]) == 1
        assert result["intent_history"][0]["intent"] == "文档分析"

    @pytest.mark.asyncio
    async def test_exception_fallback_appends_to_history(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("LLM error")
        node = IntentRecognitionNode(llm=mock_llm)
        state = self._make_state(message="测试异常", intent_history=[])

        result = await node.execute(state)

        assert result["intent"] == "问答"
        assert result["confidence"] == 0.5
        assert len(result["intent_history"]) == 1
        assert result["intent_history"][0]["intent"] == "问答"
