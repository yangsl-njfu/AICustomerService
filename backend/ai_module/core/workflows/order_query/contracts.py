"""Order query workflow contracts."""
from __future__ import annotations

from enum import Enum


class OrderQueryMode(str, Enum):
    LIST = "list"
    DETAIL = "detail"
