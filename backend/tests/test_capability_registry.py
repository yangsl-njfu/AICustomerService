from ai_module.core.capability_registry import find_unsupported_capability


def test_matches_disabled_coupon_capability():
    match = find_unsupported_capability(
        "我有优惠券可以用吗",
        features={"coupon_system": False},
    )

    assert match is not None
    assert match["key"] == "coupon_query"
    assert match["label"] == "优惠券"


def test_enabled_capability_does_not_return_unsupported_match():
    match = find_unsupported_capability(
        "我有优惠券可以用吗",
        features={"coupon_system": True},
    )

    assert match is None
