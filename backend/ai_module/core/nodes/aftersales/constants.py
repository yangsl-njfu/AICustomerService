"""Shared constants for aftersales step nodes."""
from __future__ import annotations

REASON_OPTIONS = {
    "refund_only": [
        ("quality_issue", "质量问题"),
        ("not_as_described", "与描述不符"),
        ("no_longer_needed", "不想要了"),
        ("other", "其他原因"),
    ],
    "return_refund": [
        ("quality_issue", "质量问题"),
        ("not_as_described", "与描述不符"),
        ("wrong_item", "发错商品"),
        ("missing_parts", "缺少部件"),
        ("other", "其他原因"),
    ],
    "exchange": [
        ("quality_issue", "质量问题"),
        ("wrong_item", "发错商品"),
        ("missing_parts", "缺少部件"),
        ("other", "其他原因"),
    ],
}

TYPE_LABELS = {
    "refund_only": "仅退款",
    "return_refund": "退货退款",
    "exchange": "换货",
}

REASON_LABELS = {
    "quality_issue": "质量问题",
    "not_as_described": "与描述不符",
    "wrong_item": "发错商品",
    "missing_parts": "缺少部件",
    "no_longer_needed": "不想要了",
    "other": "其他原因",
}

ORDER_STATUS_MAP = {
    "paid": "已支付",
    "delivered": "已送达",
    "completed": "已完成",
}
