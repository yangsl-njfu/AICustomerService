"""Capability registry and unsupported-capability matching helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class CapabilitySpec:
    key: str
    label: str
    keywords: tuple[str, ...]
    feature_flag: str | None = None
    enabled_by_default: bool = True
    fallback_action: Dict[str, Any] | None = None


DEFAULT_CAPABILITY_SPECS: tuple[CapabilitySpec, ...] = (
    CapabilitySpec(
        key="cart_query",
        label="购物车",
        keywords=("购物车", "购物袋", "购物清单", "购物车里", "车里有", "加入购物车"),
        feature_flag="cart_query",
        enabled_by_default=False,
        fallback_action={
            "type": "button",
            "label": "查看购物车",
            "action": "navigate",
            "data": {"path": "/cart"},
            "icon": "🛒",
            "color": "primary",
        },
    ),
    CapabilitySpec(
        key="coupon_query",
        label="优惠券",
        keywords=("优惠券", "优惠码", "折扣券", "代金券", "满减券", "券码"),
        feature_flag="coupon_system",
        enabled_by_default=False,
    ),
    CapabilitySpec(
        key="invoice_service",
        label="发票",
        keywords=("发票", "开票", "电子发票", "纸质发票"),
        feature_flag="invoice_service",
        enabled_by_default=False,
    ),
    CapabilitySpec(
        key="points_service",
        label="积分",
        keywords=("积分", "会员积分", "积分兑换"),
        feature_flag="points_system",
        enabled_by_default=False,
    ),
)


def _normalize_spec(raw: Dict[str, Any]) -> CapabilitySpec | None:
    key = str(raw.get("key") or "").strip()
    label = str(raw.get("label") or "").strip()
    keywords = tuple(str(item).strip() for item in raw.get("keywords") or [] if str(item).strip())
    if not key or not label or not keywords:
        return None

    feature_flag = raw.get("feature_flag")
    if feature_flag is not None:
        feature_flag = str(feature_flag).strip() or None

    fallback_action = raw.get("fallback_action")
    if fallback_action is not None and not isinstance(fallback_action, dict):
        fallback_action = None

    return CapabilitySpec(
        key=key,
        label=label,
        keywords=keywords,
        feature_flag=feature_flag,
        enabled_by_default=bool(raw.get("enabled_by_default", True)),
        fallback_action=fallback_action,
    )


def build_capability_specs(config: Optional[Dict[str, Any]] = None) -> tuple[CapabilitySpec, ...]:
    specs: Dict[str, CapabilitySpec] = {spec.key: spec for spec in DEFAULT_CAPABILITY_SPECS}
    custom_specs: Iterable[Dict[str, Any]] = (config or {}).get("capability_registry") or []

    for raw in custom_specs:
        if not isinstance(raw, dict):
            continue
        spec = _normalize_spec(raw)
        if spec is None:
            continue
        specs[spec.key] = spec

    return tuple(specs.values())


def is_capability_enabled(spec: CapabilitySpec, features: Optional[Dict[str, Any]] = None) -> bool:
    if spec.feature_flag:
        return bool((features or {}).get(spec.feature_flag, spec.enabled_by_default))
    return spec.enabled_by_default


def find_unsupported_capability(
    message: str,
    *,
    features: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    normalized = (message or "").strip().lower()
    if not normalized:
        return None

    best_match: tuple[tuple[int, int, int], CapabilitySpec, list[str]] | None = None
    for spec in build_capability_specs(config):
        matched = [keyword for keyword in spec.keywords if keyword and keyword.lower() in normalized]
        if not matched:
            continue
        if is_capability_enabled(spec, features):
            continue

        score = (
            len(matched),
            max(len(keyword) for keyword in matched),
            sum(len(keyword) for keyword in matched),
        )
        if best_match is None or score > best_match[0]:
            best_match = (score, spec, matched)

    if best_match is None:
        return None

    _, spec, matched = best_match
    return {
        "key": spec.key,
        "label": spec.label,
        "feature_flag": spec.feature_flag,
        "matched_keywords": matched,
        "fallback_action": dict(spec.fallback_action) if spec.fallback_action else None,
    }
