"""Lazy exports for the AI service package.

Avoid importing the whole workflow/runtime stack when a caller only needs a
single submodule such as ``ai_module.core.nodes.message_entry_node``.
"""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "runtime_factory": (".runtime", "runtime_factory"),
    "AIWorkflow": (".workflow", "AIWorkflow"),
    "ai_workflow": (".workflow", "ai_workflow"),
}


def __getattr__(name: str):
    module_name, attr_name = _EXPORTS.get(name, (None, None))
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name, __name__)
    return getattr(module, attr_name)


__all__ = list(_EXPORTS)

