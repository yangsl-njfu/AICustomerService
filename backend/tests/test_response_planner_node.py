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

for name in ["response_planner_node", "conversation_control_node"]:
    module_path = os.path.join(_backend_dir, "services", "ai", "nodes", f"{name}.py")
    module_name = f"backend.services.ai.nodes.{name}"
    spec = importlib.util.spec_from_file_location(module_name, module_path, submodule_search_locations=[])
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "backend.services.ai.nodes"
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)

ResponsePlannerNode = sys.modules["backend.services.ai.nodes.response_planner_node"].ResponsePlannerNode
ConversationControlNode = sys.modules["backend.services.ai.nodes.conversation_control_node"].ConversationControlNode


def _make_state(**overrides):
    state = {
        "has_active_flow": True,
        "active_flow": "推荐",
        "current_step": "select_recommended_item",
        "pending_question": "这些里你更喜欢哪一个？",
        "pending_action": "select_recommended_item",
        "inflow_type": None,
        "response_mode": None,
        "resume_mode": None,
        "continue_previous_task": False,
        "need_clarification": False,
        "self_contained_request": False,
        "intent": None,
        "domain_intent": None,
        "user_message": "我想去旅行",
        "conversation_history": [],
    }
    state.update(overrides)
    return state


class _FakeLLM:
    def __init__(self, content: str):
        self.content = content

    async def ainvoke(self, _messages):
        return types.SimpleNamespace(content=self.content)


class TestResponsePlannerNode:
    @pytest.mark.asyncio
    async def test_irrelevant_input_goes_to_answer_then_resume(self):
        node = ResponsePlannerNode()
        state = _make_state(inflow_type="irrelevant")

        result = await node.execute(state)

        assert result["response_mode"] == "answer_then_resume"
        assert result["resume_mode"] == "resume_exact"
        assert result["continue_previous_task"] is False

    @pytest.mark.asyncio
    async def test_related_blocker_uses_safe_step_resume(self):
        node = ResponsePlannerNode()
        state = _make_state(
            inflow_type="related_blocker",
            user_message="我不会操作这一步",
        )

        result = await node.execute(state)

        assert result["response_mode"] == "help_current_task"
        assert result["resume_mode"] == "resume_from_safe_step"

    @pytest.mark.asyncio
    async def test_unknown_self_contained_message_prefers_answer_then_resume(self):
        node = ResponsePlannerNode()
        state = _make_state(
            inflow_type="unknown",
            self_contained_request=True,
            user_message="今天天气真好",
        )

        result = await node.execute(state)

        assert result["response_mode"] == "answer_then_resume"
        assert result["resume_mode"] == "resume_exact"

    @pytest.mark.asyncio
    async def test_unknown_ambiguous_reference_still_clarifies(self):
        node = ResponsePlannerNode()
        state = _make_state(
            inflow_type="unknown",
            user_message="那个呢",
        )

        result = await node.execute(state)

        assert result["response_mode"] == "clarify_before_resume"
        assert result["resume_mode"] == "resume_from_safe_step"

    @pytest.mark.asyncio
    async def test_conversation_control_generates_resume_prompt(self):
        node = ConversationControlNode()
        state = _make_state(
            response_mode="clarify_before_resume",
            resume_mode="resume_exact",
            user_message="那个呢",
        )

        result = await node.execute(state)

        assert "那个呢" in result["response"]
        assert "第一个" in result["response"]
        assert "切换" not in result["response"]

    @pytest.mark.asyncio
    async def test_conversation_control_answers_side_topic_naturally(self):
        node = ConversationControlNode(llm=_FakeLLM("这句我先接住，刚才那个推荐我也还记着。"))
        state = _make_state(
            response_mode="answer_then_resume",
            user_message="今天天气真好",
        )

        result = await node.execute(state)

        assert "刚才那个推荐" in result["response"]
