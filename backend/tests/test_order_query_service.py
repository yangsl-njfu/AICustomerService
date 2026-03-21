import pytest

from ai_module.core.workflows.order_query.service import OrderQueryService


class TestOrderQueryService:
    @pytest.mark.asyncio
    async def test_cart_question_does_not_fall_back_to_order_selector(self):
        service = OrderQueryService()
        state = {
            "user_message": "购物车有东西吗",
            "user_id": "u1",
        }

        result = await service.handle_list_orders(state)

        assert "购物车" in result["response"]
        assert result["quick_actions"][0]["action"] == "navigate"
        assert result["quick_actions"][0]["data"]["path"] == "/cart"
