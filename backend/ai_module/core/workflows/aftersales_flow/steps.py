"""Composable node helpers for aftersales workflow."""
from __future__ import annotations

from typing import Dict

from ...nodes.aftersales import (
    AftersalesCancelNode,
    AftersalesConfirmNode,
    AftersalesInputDescriptionNode,
    AftersalesResultNode,
    AftersalesSelectOrderNode,
    AftersalesSelectReasonNode,
    AftersalesSelectTypeNode,
    AftersalesSubmitNode,
)
from ...nodes.common.base import BaseNode
from ...state import ConversationState


def build_step_nodes() -> Dict[str, BaseNode]:
    return {
        "select_order": AftersalesSelectOrderNode(),
        "select_type": AftersalesSelectTypeNode(),
        "select_reason": AftersalesSelectReasonNode(),
        "input_description": AftersalesInputDescriptionNode(),
        "confirm": AftersalesConfirmNode(),
        "submit": AftersalesSubmitNode(),
        "result": AftersalesResultNode(),
        "cancel": AftersalesCancelNode(),
    }


def cleanup_runtime_keys(state: ConversationState) -> ConversationState:
    state.pop("_aftersales_step", None)
    state.pop("_aftersales_node_key", None)
    return state
