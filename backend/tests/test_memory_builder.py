import importlib.util
import os
import sys
import types


_backend_dir = os.path.join(os.path.dirname(__file__), "..")

for pkg in [
    "backend",
    "backend.services",
    "backend.services.ai",
]:
    if pkg not in sys.modules:
        sys.modules[pkg] = types.ModuleType(pkg)

_module_path = os.path.join(_backend_dir, "services", "ai", "memory_builder.py")
_module_name = "backend.services.ai.memory_builder"
_spec = importlib.util.spec_from_file_location(_module_name, _module_path)
_mod = importlib.util.module_from_spec(_spec)
_mod.__package__ = "backend.services.ai"
sys.modules[_module_name] = _mod
_spec.loader.exec_module(_mod)

MemoryContextBuilder = _mod.MemoryContextBuilder


def test_recent_history_uses_short_term_window():
    builder = MemoryContextBuilder(recent_turn_limit=4)
    history = [
        {"user": f"user-{index}", "assistant": f"assistant-{index}"}
        for index in range(1, 7)
    ]

    result = builder.build_recent_history_text(history)

    assert "user-1" not in result
    assert "assistant-1" not in result
    assert "user-3" in result
    assert "assistant-6" in result


def test_short_term_memory_includes_task_snapshot():
    builder = MemoryContextBuilder(recent_turn_limit=3)
    state = {
        "conversation_history": [
            {"user": "天气真冷啊", "assistant": "是啊，这两天降温挺明显的。"},
            {"user": "我要去新疆旅行", "assistant": "新疆这个季节昼夜温差会比较大。"},
        ],
        "active_task": {
            "intent": "推荐",
            "pending_action": "select_recommended_item",
            "pending_question": "这些里你更喜欢哪一个？",
            "slots": {"language": "Python", "budget_max": 1000},
        },
        "pending_action": "select_recommended_item",
        "pending_question": "这些里你更喜欢哪一个？",
        "last_intent": "推荐",
    }

    result = builder.build_short_term_memory_text(state)

    assert "最近对话：" in result
    assert "我要去新疆旅行" in result
    assert "任务快照：" in result
    assert "当前主任务：推荐" in result
    assert "当前停留步骤：select_recommended_item" in result
    assert "language=Python" in result
