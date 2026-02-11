"""
Unit tests for QANode conversation_summary injection.

Tests verify that:
- Non-empty conversation_summary is injected into the RAG prompt
- Empty conversation_summary results in no summary section in the prompt
- The summary is clearly labeled in the prompt
"""
import sys
import os
import types
import importlib.util
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Bootstrap: set up module hierarchy so qa_node imports work ──

_backend_dir = os.path.join(os.path.dirname(__file__), "..")

for pkg in [
    "backend",
    "backend.services",
    "backend.services.ai",
    "backend.services.ai.nodes",
]:
    if pkg not in sys.modules:
        sys.modules[pkg] = types.ModuleType(pkg)

# Stub config
_config_path = os.path.join(_backend_dir, "config.py")
_config_spec = importlib.util.spec_from_file_location("backend.config", _config_path)
_config_mod = importlib.util.module_from_spec(_config_spec)
sys.modules["backend.config"] = _config_mod
sys.modules["config"] = _config_mod
_config_spec.loader.exec_module(_config_mod)

# Stub knowledge_retriever
_kr_mod = types.ModuleType("services.knowledge_retriever")
_mock_retriever = MagicMock()
_mock_retriever.retrieve = AsyncMock(return_value=[])
_kr_mod.knowledge_retriever = _mock_retriever
sys.modules["services.knowledge_retriever"] = _kr_mod

# Stub file_service
_fs_mod = types.ModuleType("services.file_service")
_fs_mod.FileService = MagicMock
sys.modules["services.file_service"] = _fs_mod

# Stub base node
_base_mod = types.ModuleType("backend.services.ai.nodes.base")


class _FakeBaseNode:
    def __init__(self, llm=None):
        self.llm = llm


_base_mod.BaseNode = _FakeBaseNode
sys.modules["backend.services.ai.nodes.base"] = _base_mod
sys.modules["services.ai.nodes.base"] = _base_mod

# Stub state
_state_path = os.path.join(_backend_dir, "services", "ai", "state.py")
if os.path.exists(_state_path):
    _state_spec = importlib.util.spec_from_file_location("backend.services.ai.state", _state_path)
    _state_mod = importlib.util.module_from_spec(_state_spec)
    sys.modules["backend.services.ai.state"] = _state_mod
    _state_spec.loader.exec_module(_state_mod)
else:
    _state_mod = types.ModuleType("backend.services.ai.state")
    _state_mod.ConversationState = dict
    sys.modules["backend.services.ai.state"] = _state_mod

# Now load qa_node
_qa_path = os.path.join(_backend_dir, "services", "ai", "nodes", "qa_node.py")
_qa_spec = importlib.util.spec_from_file_location("backend.services.ai.nodes.qa_node", _qa_path)
_qa_mod = importlib.util.module_from_spec(_qa_spec)
_qa_mod.__package__ = "backend.services.ai.nodes"
sys.modules["backend.services.ai.nodes.qa_node"] = _qa_mod
_qa_spec.loader.exec_module(_qa_mod)

QANode = _qa_mod.QANode
RAG_PROMPT = _qa_mod.RAG_PROMPT


# ── Helpers ──────────────────────────────────────────────────────────

def _make_state(user_message="请问这个商品怎么样？", conversation_summary="", **overrides):
    state = {
        "user_message": user_message,
        "conversation_history": [],
        "conversation_summary": conversation_summary,
        "attachments": [],
        "retrieved_docs": [],
        "sources": [],
    }
    state.update(overrides)
    return state


# ── Tests ────────────────────────────────────────────────────────────

class TestQANodeSummaryInjection:
    @pytest.mark.asyncio
    async def test_summary_injected_when_present(self):
        """Non-empty conversation_summary should appear in the prompt."""
        summary_text = "用户之前咨询了订单ORD123的物流状态"
        state = _make_state(conversation_summary=summary_text)
        node = QANode(llm=MagicMock())

        messages = await node._prepare_messages(state)

        system_content = messages[0].content
        assert "对话历史摘要" in system_content
        assert summary_text in system_content

    @pytest.mark.asyncio
    async def test_no_summary_section_when_empty(self):
        """Empty conversation_summary should not add a summary section."""
        state = _make_state(conversation_summary="")
        node = QANode(llm=MagicMock())

        messages = await node._prepare_messages(state)

        system_content = messages[0].content
        assert "对话历史摘要" not in system_content

    @pytest.mark.asyncio
    async def test_no_summary_section_when_missing(self):
        """Missing conversation_summary key should not add a summary section."""
        state = _make_state()
        del state["conversation_summary"]
        node = QANode(llm=MagicMock())

        messages = await node._prepare_messages(state)

        system_content = messages[0].content
        assert "对话历史摘要" not in system_content

    @pytest.mark.asyncio
    async def test_chitchat_skips_rag_prompt(self):
        """Chitchat messages should use SIMPLE_PROMPT, not RAG_PROMPT with summary."""
        state = _make_state(user_message="你好", conversation_summary="一些摘要内容")
        node = QANode(llm=MagicMock())

        messages = await node._prepare_messages(state)

        system_content = messages[0].content
        assert "对话历史摘要" not in system_content
