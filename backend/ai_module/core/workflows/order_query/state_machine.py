"""State machine for order query workflow."""
from __future__ import annotations

from enum import Enum


class OrderQueryState(str, Enum):
    START = "start"
    RESOLVE_MODE = "resolve_mode"
    EXECUTE_MODE = "execute_mode"
    CLEANUP = "cleanup"
    END = "end"


PIPELINE_TRANSITIONS = {
    OrderQueryState.START: OrderQueryState.RESOLVE_MODE,
    OrderQueryState.RESOLVE_MODE: OrderQueryState.EXECUTE_MODE,
    OrderQueryState.EXECUTE_MODE: OrderQueryState.CLEANUP,
    OrderQueryState.CLEANUP: OrderQueryState.END,
}


def next_state(current: OrderQueryState) -> OrderQueryState:
    return PIPELINE_TRANSITIONS[current]
