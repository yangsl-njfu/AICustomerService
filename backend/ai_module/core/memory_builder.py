"""短期记忆组装器。

职责：
- 从单个会话的最近几轮历史中提取短期上下文
- 把当前任务停留点、待回答问题等状态拼成可直接喂给模型的记忆块

这里不做长期偏好记忆，也不负责跨会话画像，只服务于当前会话里的短期承接。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class MemoryContextBuilder:
    """把最近几轮对话和任务快照组装成统一的短期记忆视图。"""

    def __init__(self, recent_turn_limit: int = 6):
        self.recent_turn_limit = recent_turn_limit

    def build_recent_history_text(
        self,
        history: List[Dict[str, Any]],
        limit: Optional[int] = None,
    ) -> str:
        if not history:
            return "（无）"

        turn_limit = limit or self.recent_turn_limit
        lines: List[str] = []
        for turn in history[-turn_limit:]:
            lines.append(f"用户：{turn.get('user', '')}")
            lines.append(f"助手：{turn.get('assistant', '')}")
        return "\n".join(lines)

    def build_task_snapshot_text(self, state: Dict[str, Any]) -> str:
        active_task = state.get("active_task") or {}
        slots = active_task.get("slots") or {}

        task_intent = (
            active_task.get("intent")
            or state.get("active_flow")
            or state.get("last_intent")
        )
        current_step = (
            state.get("current_step")
            or active_task.get("pending_action")
            or state.get("pending_action")
        )
        pending_question = (
            active_task.get("pending_question")
            or state.get("pending_question")
        )

        lines: List[str] = []
        if task_intent:
            lines.append(f"当前主任务：{task_intent}")
        if current_step:
            lines.append(f"当前停留步骤：{current_step}")
        if pending_question:
            lines.append(f"当前待回答问题：{pending_question}")

        filled_slots = {key: value for key, value in slots.items() if value not in (None, "", [], {})}
        if filled_slots:
            slot_pairs = "，".join(f"{key}={value}" for key, value in list(filled_slots.items())[:6])
            lines.append(f"当前已知约束：{slot_pairs}")

        return "\n".join(lines) if lines else "（无）"

    def build_short_term_memory_text(
        self,
        state: Dict[str, Any],
        *,
        include_task_snapshot: bool = True,
        limit: Optional[int] = None,
    ) -> str:
        sections = [
            "最近对话：",
            self.build_recent_history_text(state.get("conversation_history") or [], limit=limit),
        ]

        if include_task_snapshot:
            sections.extend(
                [
                    "",
                    "任务快照：",
                    self.build_task_snapshot_text(state),
                ]
            )

        return "\n".join(sections)
