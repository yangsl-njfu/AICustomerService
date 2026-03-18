import importlib.util
import os
import sys
import types

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
_constants_mod.__package__ = "backend.services.ai"
sys.modules["backend.services.ai.constants"] = _constants_mod
_constants_spec.loader.exec_module(_constants_mod)

for name in ["intent_node", "turn_understanding_node", "message_entry_node"]:
    module_path = os.path.join(_backend_dir, "services", "ai", "nodes", f"{name}.py")
    module_name = f"backend.services.ai.nodes.{name}"
    spec = importlib.util.spec_from_file_location(module_name, module_path, submodule_search_locations=[])
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "backend.services.ai.nodes"
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)

MessageEntryNode = sys.modules["backend.services.ai.nodes.message_entry_node"].MessageEntryNode


def _make_state(message: str, **overrides):
    state = {
        "user_message": message,
        "user_id": "u1",
        "session_id": "s1",
        "attachments": [],
        "conversation_history": [],
        "user_profile": {},
        "last_intent": None,
        "last_quick_actions": [],
        "active_task": None,
        "task_stack": [],
        "pending_question": None,
        "pending_action": None,
        "intent_history": [],
        "conversation_summary": "",
        "purchase_flow": None,
        "aftersales_flow": None,
    }
    state.update(overrides)
    return state


class TestMessageEntryNode:
    @pytest.mark.asyncio
    async def test_without_active_flow_uses_global_intent_classifier(self):
        node = MessageEntryNode()
        state = _make_state("帮我推荐几个 Java 项目")

        result = await node.execute(state)

        assert result["entry_classifier"] == "global_intent"
        assert result["has_active_flow"] is False
        assert result["intent"] == "推荐"
        assert result["domain_intent"] == "推荐"
        assert result["dialogue_act"] == "new_request"
        assert result["self_contained_request"] is True

    @pytest.mark.asyncio
    async def test_with_active_flow_uses_inflow_classifier_for_continuation(self):
        node = MessageEntryNode()
        state = _make_state(
            "800以内，Java的，简单点",
            last_intent="推荐",
            active_task={"intent": "推荐", "status": "awaiting_user"},
            pending_action="select_recommended_item",
            pending_question="这些里你更喜欢哪一个？",
            conversation_history=[
                {"user": "帮我推荐几个 Java 项目", "assistant": "告诉我你的预算和技术偏好。"}
            ],
        )

        result = await node.execute(state)

        assert result["entry_classifier"] == "inflow"
        assert result["has_active_flow"] is True
        assert result["active_flow"] == "推荐"
        assert result["inflow_type"] == "valid_current_input"
        assert result["intent"] == "推荐"
        assert result["continue_previous_task"] is True
        assert result["slot_updates"]["budget_max"] == 800
        assert result["slot_updates"]["language"] == "Java"

    @pytest.mark.asyncio
    async def test_with_active_flow_switches_to_new_global_intent_when_user_changes_task(self):
        node = MessageEntryNode()
        state = _make_state(
            "查一下我的订单",
            last_intent="推荐",
            active_task={"intent": "推荐", "status": "awaiting_user"},
            pending_action="select_recommended_item",
            pending_question="这些里你更喜欢哪一个？",
            conversation_history=[
                {"user": "帮我推荐几个 Java 项目", "assistant": "我给你推荐了 3 个方向。"}
            ],
        )

        result = await node.execute(state)

        assert result["entry_classifier"] == "inflow"
        assert result["has_active_flow"] is True
        assert result["inflow_type"] == "switch_flow"
        assert result["flow_relation"] == "switch"
        assert result["intent"] == "订单查询"
        assert result["domain_intent"] == "订单查询"
        assert result["continue_previous_task"] is False

    @pytest.mark.asyncio
    async def test_same_domain_self_contained_request_defers_to_inflow_llm(self):
        node = MessageEntryNode()
        state = _make_state(
            "我想去旅行",
            last_intent="推荐",
            active_task={"intent": "推荐", "status": "awaiting_user"},
            pending_action="select_recommended_item",
            pending_question="这些里你更喜欢哪一个？",
            conversation_history=[
                {"user": "帮我推荐几个 Java 项目", "assistant": "我先给你 3 个方向。"}
            ],
        )

        async def fake_understanding(_state):
            _state["dialogue_act"] = "new_request"
            _state["domain_intent"] = "推荐"
            _state["self_contained_request"] = True
            _state["continue_previous_task"] = False
            _state["slot_updates"] = {}
            _state["understanding_confidence"] = 0.72
            return _state

        async def fake_inflow_llm(*_args, **_kwargs):
            return {
                "inflow_type": "irrelevant",
                "domain_intent": None,
                "continue_previous_task": False,
                "need_clarification": False,
                "confidence": 0.84,
            }

        node.inflow_understanding.execute = fake_understanding
        node._infer_inflow_with_llm = fake_inflow_llm

        result = await node.execute(state)

        assert result["inflow_type"] == "irrelevant"
        assert result["flow_relation"] == "interrupt"
        assert result["continue_previous_task"] is False
