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

_node_path = os.path.join(_backend_dir, "services", "ai", "nodes", "dialogue_state_node.py")
_node_spec = importlib.util.spec_from_file_location(
    "backend.services.ai.nodes.dialogue_state_node",
    _node_path,
)
_node_mod = importlib.util.module_from_spec(_node_spec)
_node_mod.__package__ = "backend.services.ai.nodes"
sys.modules["backend.services.ai.nodes.dialogue_state_node"] = _node_mod
_node_spec.loader.exec_module(_node_mod)

DialogueStateNode = _node_mod.DialogueStateNode


def _make_state(**overrides):
    state = {
        "timestamp": "2026-03-17T10:00:00",
        "user_message": "需要",
        "intent": "推荐",
        "dialogue_act": "confirm",
        "continue_previous_task": True,
        "slot_updates": {},
        "selected_quick_action": None,
        "active_task": {
            "id": "task-1",
            "intent": "推荐",
            "status": "awaiting_user",
            "slots": {"language": "Java"},
        },
        "task_stack": [],
        "pending_question": "需要我继续帮你搜索吗？",
        "pending_action": "answer_follow_up",
    }
    state.update(overrides)
    return state


class TestDialogueStateNode:
    @pytest.mark.asyncio
    async def test_continue_previous_task_merges_slots(self):
        node = DialogueStateNode()
        state = _make_state(slot_updates={"budget_max": 800})

        result = await node.execute(state)

        assert result["active_task"]["intent"] == "推荐"
        assert result["active_task"]["slots"]["language"] == "Java"
        assert result["active_task"]["slots"]["budget_max"] == 800
        assert result["pending_question"] is None
        assert result["pending_action"] is None

    @pytest.mark.asyncio
    async def test_new_request_suspends_previous_task(self):
        node = DialogueStateNode()
        state = _make_state(
            user_message="先帮我查订单",
            intent="订单查询",
            dialogue_act="switch_topic",
            continue_previous_task=False,
        )

        result = await node.execute(state)

        assert result["active_task"]["intent"] == "订单查询"
        assert len(result["task_stack"]) == 1
        assert result["task_stack"][0]["intent"] == "推荐"
        assert result["task_stack"][0]["status"] == "suspended"

    @pytest.mark.asyncio
    async def test_resume_task_restores_from_stack(self):
        node = DialogueStateNode()
        state = _make_state(
            user_message="继续刚才那个",
            intent="推荐",
            dialogue_act="resume_task",
            continue_previous_task=True,
            active_task={
                "id": "task-2",
                "intent": "订单查询",
                "status": "active",
                "slots": {"selected_order_no": "ORD001"},
            },
            task_stack=[
                {
                    "id": "task-1",
                    "intent": "推荐",
                    "status": "suspended",
                    "slots": {"language": "Java", "budget_max": 800},
                }
            ],
        )

        result = await node.execute(state)

        assert result["active_task"]["intent"] == "推荐"
        assert result["active_task"]["slots"]["language"] == "Java"
        assert result["active_task"]["slots"]["budget_max"] == 800
        assert len(result["task_stack"]) == 1
        assert result["task_stack"][0]["intent"] == "订单查询"

    @pytest.mark.asyncio
    async def test_selected_action_is_folded_into_task_slots(self):
        node = DialogueStateNode()
        state = _make_state(
            user_message="第一个",
            dialogue_act="select_item",
            selected_quick_action={
                "type": "product",
                "data": {
                    "product_id": 42,
                    "title": "Java 图书管理系统",
                },
            },
        )

        result = await node.execute(state)

        assert result["active_task"]["slots"]["selected_product_id"] == 42
        assert result["active_task"]["slots"]["selected_product_title"] == "Java 图书管理系统"
