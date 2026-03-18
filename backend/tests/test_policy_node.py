import os
import sys
import types
import importlib.util

import pytest

_backend_dir = os.path.join(os.path.dirname(__file__), "..")

for pkg in [
    "backend",
    "backend.services",
    "backend.services.ai",
    "backend.services.ai.nodes",
]:
    if pkg not in sys.modules:
        sys.modules[pkg] = types.ModuleType(pkg)

_state_path = os.path.join(_backend_dir, "services", "ai", "state.py")
_state_spec = importlib.util.spec_from_file_location("backend.services.ai.state", _state_path)
_state_mod = importlib.util.module_from_spec(_state_spec)
sys.modules["backend.services.ai.state"] = _state_mod
_state_spec.loader.exec_module(_state_mod)

_base_path = os.path.join(_backend_dir, "services", "ai", "nodes", "base.py")
_base_spec = importlib.util.spec_from_file_location("backend.services.ai.nodes.base", _base_path)
_base_mod = importlib.util.module_from_spec(_base_spec)
sys.modules["backend.services.ai.nodes.base"] = _base_mod
_base_spec.loader.exec_module(_base_mod)

_constants_path = os.path.join(_backend_dir, "services", "ai", "constants.py")
_constants_spec = importlib.util.spec_from_file_location("backend.services.ai.constants", _constants_path)
_constants_mod = importlib.util.module_from_spec(_constants_spec)
sys.modules["backend.services.ai.constants"] = _constants_mod
_constants_spec.loader.exec_module(_constants_mod)

_node_path = os.path.join(_backend_dir, "services", "ai", "nodes", "policy_node.py")
_node_spec = importlib.util.spec_from_file_location(
    "backend.services.ai.nodes.policy_node",
    _node_path,
)
_node_mod = importlib.util.module_from_spec(_node_spec)
_node_mod.__package__ = "backend.services.ai.nodes"
sys.modules["backend.services.ai.nodes.policy_node"] = _node_mod
_node_spec.loader.exec_module(_node_mod)

PolicyNode = _node_mod.PolicyNode


def _make_state(**overrides):
    state = {
        "dialogue_act": "new_request",
        "domain_intent": None,
        "self_contained_request": False,
        "continue_previous_task": False,
        "need_clarification": False,
        "understanding_confidence": 0.0,
        "intent": None,
        "confidence": None,
        "last_intent": None,
        "active_task": None,
        "task_stack": [],
    }
    state.update(overrides)
    return state


class TestPolicyNode:
    @pytest.mark.asyncio
    async def test_self_contained_request_prefers_domain_intent(self):
        node = PolicyNode()
        state = _make_state(
            dialogue_act="new_request",
            domain_intent="推荐",
            self_contained_request=True,
            understanding_confidence=0.92,
            last_intent="问答",
            active_task={"intent": "问答", "status": "awaiting_user"},
        )

        result = await node.execute(state)

        assert result["intent"] == "推荐"
        assert result["confidence"] == 0.92
        assert result["continue_previous_task"] is False

    @pytest.mark.asyncio
    async def test_continuation_reuses_active_task_intent(self):
        node = PolicyNode()
        state = _make_state(
            dialogue_act="provide_slot",
            continue_previous_task=True,
            understanding_confidence=0.9,
            active_task={"intent": "推荐", "status": "awaiting_user"},
            last_intent="推荐",
        )

        result = await node.execute(state)

        assert result["intent"] == "推荐"
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_conflicting_hint_breaks_continuation_bias(self):
        node = PolicyNode()
        state = _make_state(
            dialogue_act="provide_slot",
            domain_intent="订单查询",
            continue_previous_task=True,
            understanding_confidence=0.86,
            active_task={"intent": "问答", "status": "awaiting_user"},
            last_intent="问答",
        )

        result = await node.execute(state)

        assert result["intent"] == "订单查询"
        assert result["dialogue_act"] == "new_request"
        assert result["continue_previous_task"] is False
        assert result["self_contained_request"] is True

    @pytest.mark.asyncio
    async def test_unclear_turn_keeps_intent_empty_for_clarification(self):
        node = PolicyNode()
        state = _make_state(
            dialogue_act="unclear",
            need_clarification=True,
            understanding_confidence=0.25,
        )

        result = await node.execute(state)

        assert result["intent"] is None
        assert result["confidence"] == 0.25
