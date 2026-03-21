"""State machine for document analysis workflow."""
from __future__ import annotations

from enum import Enum


class DocumentAnalysisState(str, Enum):
    START = "start"
    EXTRACT = "extract"
    RESPOND = "respond"
    END = "end"


PIPELINE_TRANSITIONS = {
    DocumentAnalysisState.START: DocumentAnalysisState.EXTRACT,
    DocumentAnalysisState.EXTRACT: DocumentAnalysisState.RESPOND,
    DocumentAnalysisState.RESPOND: DocumentAnalysisState.END,
}


def next_state(current: DocumentAnalysisState) -> DocumentAnalysisState:
    return PIPELINE_TRANSITIONS[current]
