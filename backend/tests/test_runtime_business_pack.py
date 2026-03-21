from ai_module.core.constants import INTENT_CART_QUERY, INTENT_ORDER_QUERY
from ai_module.core.runtime import BusinessPack


def test_business_pack_merges_default_intent_labels_and_rules():
    pack = BusinessPack(
        "demo",
        {
            "intent_classifier": {
                "labels": ["问答", "订单查询"],
                "rules": {
                    INTENT_ORDER_QUERY: ["查订单"],
                },
            }
        },
    )

    labels = pack.get_intent_labels()
    rules = pack.get_intent_rules()

    assert INTENT_CART_QUERY in labels
    assert "购物车" in rules[INTENT_CART_QUERY]
    assert "查订单" in rules[INTENT_ORDER_QUERY]
