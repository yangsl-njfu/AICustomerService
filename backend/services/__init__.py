"""Lazy service package exports.

Avoid importing unrelated service dependencies when only a subpackage such as
`services.ai` is needed.
"""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "AuthService": ".auth_service",
    "SessionService": ".session_service",
    "MessageService": ".message_service",
    "TicketService": ".ticket_service",
    "FileService": ".file_service",
}


def __getattr__(name: str):
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name, __name__)
    return getattr(module, name)


__all__ = list(_EXPORTS)
