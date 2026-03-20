"""
购买流程节点 - 处理选品→加购物车→优惠券→地址→下单支付全流程
"""
import logging
from .base import BaseNode
from ..state import ConversationState

logger = logging.getLogger(__name__)


class PurchaseFlowNode(BaseNode):
    """购买流程节点"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行购买流程"""
        
        purchase_flow = state.get("purchase_flow", {})
        step = purchase_flow.get("step", "start") if purchase_flow else "start"
        
        logger.info(f"🛒 [PurchaseFlowNode] step={step}, flow_data={purchase_flow}")
        
        if not purchase_flow or step == "start":
            return state
        
        if step == "confirm_product":
            return await self.handle_confirm_product(state, purchase_flow)
        elif step == "select_coupon":
            return await self.handle_select_coupon(state, purchase_flow)
        elif step == "confirm_coupon":
            return await self.handle_confirm_coupon(state, purchase_flow)
        elif step == "select_address":
            return await self.handle_select_address(state, purchase_flow)
        elif step == "confirm_address":
            return await self.handle_confirm_address(state, purchase_flow)
        elif step == "order_confirm":
            return await self.handle_order_confirm(state, purchase_flow)
        elif step == "payment":
            return await self.handle_payment(state, purchase_flow)
        elif step == "payment_done":
            return await self.handle_payment_done(state, purchase_flow)
        elif step == "payment_success":
            return await self.handle_payment_success(state, purchase_flow)
        else:
            state["response"] = "抱歉，购买流程出现了问题，请重新开始。"
            return state
    
    async def handle_confirm_product(self, state: ConversationState, flow_data: dict):
        """步骤1: 确认商品"""
        product_id = flow_data.get("product_id")
        
        if not product_id:
            state["response"] = "请先选择要购买的商品"
            return state
        
        from database.connection import get_db_context
        from services.product_service import ProductService
        
        async with get_db_context() as db:
            product_service = ProductService(db)
            product = await product_service.get_product(product_id)
            
            if not product:
                state["response"] = "商品不存在或已下架"
                return state
            
            state["purchase_flow"] = {
                **flow_data,
                "product": {
                    "id": product.get("id"),
                    "title": product.get("title"),
                    "price": product.get("price", 0),
                    "tech_stack": product.get("tech_stack", [])
                },
                "step": "select_coupon"
            }
            
            coupons = await self.get_available_coupons(state.get("user_id"), product.get("price", 0))
            
            if coupons:
                coupon_cards = []
                for c in coupons[:3]:
                    coupon_cards.append({
                        "type": "coupon",
                        "data": {
                            "coupon_id": c["id"],
                            "name": c["name"],
                            "discount": c["discount_amount"],
                            "min_amount": c["min_amount"],
                            "expire_date": c["expire_date"]
                        }
                    })
                
                state["response"] = f"✅ 已确认商品：{product.get('title')}（¥{product.get('price', 0)}）\n\n您有 {len(coupons)} 张可用优惠券："
                state["quick_actions"] = coupon_cards + [
                    {
                        "type": "button",
                        "label": "不使用优惠券",
                        "action": "purchase_flow",
                        "data": {
                            "step": "confirm_coupon",
                            "product_id": product_id,
                            "coupon_id": None
                        },
                        "icon": "➖"
                    }
                ]
            else:
                state["response"] = f"✅ 已确认商品：{product.get('title')}（¥{product.get('price', 0)}）\n\n暂无优惠券可用，是否确认收货地址？"
                state["quick_actions"] = [
                    {
                        "type": "button",
                        "label": "选择收货地址",
                        "action": "purchase_flow",
                        "data": {
                            "step": "select_address",
                            "product_id": product_id,
                            "coupon_id": None
                        },
                        "icon": "📍"
                    }
                ]
        
        return state
    
    async def get_available_coupons(self, user_id: str, order_amount: float):
        """获取用户可用优惠券"""
        from database.connection import get_db_context
        from sqlalchemy import select
        from database.models import Coupon, UserCoupon
        from datetime import datetime
        
        async with get_db_context() as db:
            stmt = select(UserCoupon, Coupon).join(
                Coupon, UserCoupon.coupon_id == Coupon.id
            ).where(
                UserCoupon.user_id == user_id,
                UserCoupon.status == "unused",
                Coupon.min_amount <= order_amount,
                Coupon.expire_date > datetime.now()
            )
            result = await db.execute(stmt)
            rows = result.all()
            
            coupons = []
            for user_coupon, coupon in rows:
                coupons.append({
                    "id": coupon.id,
                    "name": coupon.name,
                    "discount_amount": coupon.discount_amount,
                    "min_amount": coupon.min_amount,
                    "expire_date": coupon.expire_date.strftime("%Y-%m-%d") if coupon.expire_date else ""
                })
            
            return coupons
    
    async def handle_select_coupon(self, state: ConversationState, flow_data: dict):
        """步骤2: 选择优惠券"""
        return await self.handle_confirm_product(state, {**flow_data, "step": "confirm_coupon"})
    
    async def handle_confirm_coupon(self, state: ConversationState, flow_data: dict):
        """步骤2.1: 确认优惠券选择"""
        product = flow_data.get("product", {})
        coupon_id = flow_data.get("coupon_id")
        
        from database.connection import get_db_context
        from sqlalchemy import select
        from database.models import Coupon
        
        coupon_info = None
        if coupon_id:
            async with get_db_context() as db:
                stmt = select(Coupon).where(Coupon.id == coupon_id)
                result = await db.execute(stmt)
                coupon = result.scalar_one_or_none()
                if coupon:
                    coupon_info = {
                        "id": coupon.id,
                        "name": coupon.name,
                        "discount": coupon.discount_amount / 100
                    }
        
        product_price = product.get("price", 0)
        discount = coupon_info["discount"] if coupon_info else 0
        final_price = max(0, product_price - discount)
        
        state["purchase_flow"] = {
            **flow_data,
            "coupon": coupon_info,
            "final_price": final_price,
            "step": "select_address"
        }
        
        response = f"✅ 商品已确认：{product.get('title')}（¥{product_price}）\n"
        if coupon_info:
            response += f"✅ 优惠券：{coupon_info['name']}（-¥{discount}）\n"
        response += f"\n请选择收货地址："
        
        addresses = await self.get_user_addresses(state.get("user_id"))
        
        if addresses:
            address_cards = []
            for addr in addresses[:3]:
                address_cards.append({
                    "type": "address",
                    "data": {
                        "address_id": addr["id"],
                        "contact": addr["contact"],
                        "phone": addr["phone"],
                        "address": addr["full_address"],
                        "product_id": flow_data.get("product_id"),
                        "coupon_id": coupon_id,
                        "final_price": final_price
                    }
                })

            state["response"] = response
            state["quick_actions"] = address_cards + [
                {
                    "type": "button",
                    "label": "使用默认地址",
                    "action": "purchase_flow",
                    "data": {
                        "step": "confirm_address",
                        "product_id": flow_data.get("product_id"),
                        "coupon_id": coupon_id,
                        "address_id": addresses[0]["id"] if addresses else None,
                        "product": product,
                        "coupon": coupon_info,
                        "final_price": final_price
                    },
                    "icon": "📍"
                }
            ]
        else:
            state["response"] = response + "\n\n您还没有收货地址，请先添加。"
            state["quick_actions"] = [
                {
                    "type": "button",
                    "label": "去添加地址",
                    "action": "navigate",
                    "data": {"path": "/profile/addresses"},
                    "icon": "➕"
                }
            ]
        
        return state
    
    async def get_user_addresses(self, user_id: str):
        """获取用户收货地址"""
        from database.connection import get_db_context
        from sqlalchemy import select
        from database.models import Address
        
        async with get_db_context() as db:
            stmt = select(Address).where(
                Address.user_id == user_id
            ).order_by(Address.is_default.desc())
            result = await db.execute(stmt)
            addresses = result.scalars().all()
            
            return [
                {
                    "id": a.id,
                    "contact": a.contact,
                    "phone": a.phone,
                    "province": a.province,
                    "city": a.city,
                    "district": a.district,
                    "detail": a.detail,
                    "full_address": f"{a.province}{a.city}{a.district}{a.detail}"
                }
                for a in addresses
            ]
    
    async def handle_select_address(self, state: ConversationState, flow_data: dict):
        """步骤3: 选择地址 - 展示地址列表供用户选择"""
        product = flow_data.get("product")
        product_id = flow_data.get("product_id")
        coupon = flow_data.get("coupon")
        coupon_id = flow_data.get("coupon_id")
        final_price = flow_data.get("final_price")

        # 如果当前没有商品详情，就根据商品编号补查一次。
        if not product and product_id:
            from database.connection import get_db_context
            from services.product_service import ProductService

            async with get_db_context() as db:
                product_service = ProductService(db)
                product_data = await product_service.get_product(product_id)
                if product_data:
                    product = {
                        "id": product_data.get("id"),
                        "title": product_data.get("title"),
                        "price": product_data.get("price", 0)
                    }

        if final_price is None and product:
            final_price = product.get("price", 0)

        state["purchase_flow"] = {
            **flow_data,
            "product": product,
            "step": "select_address"
        }

        addresses = await self.get_user_addresses(state.get("user_id"))

        response = f"请选择收货地址："

        if addresses:
            address_cards = []
            for addr in addresses[:3]:
                address_cards.append({
                    "type": "address",
                    "data": {
                        "address_id": addr["id"],
                        "contact": addr["contact"],
                        "phone": addr["phone"],
                        "address": addr["full_address"],
                        "product_id": product_id,
                        "coupon_id": coupon_id,
                        "final_price": final_price
                    }
                })

            state["response"] = response
            state["quick_actions"] = address_cards + [
                {
                    "type": "button",
                    "label": "使用默认地址",
                    "action": "purchase_flow",
                    "data": {
                        "step": "confirm_address",
                        "product_id": product_id,
                        "coupon_id": coupon_id,
                        "address_id": addresses[0]["id"],
                        "product": product,
                        "coupon": coupon,
                        "final_price": final_price
                    },
                    "icon": "📍"
                }
            ]
        else:
            state["response"] = response + "\n\n您还没有收货地址，请先添加。"
            state["quick_actions"] = [
                {
                    "type": "button",
                    "label": "去添加地址",
                    "action": "navigate",
                    "data": {"path": "/profile/addresses"},
                    "icon": "➕"
                }
            ]

        return state
    
    async def handle_confirm_address(self, state: ConversationState, flow_data: dict):
        """步骤3.1: 确认地址"""
        product = flow_data.get("product", {})
        product_id = flow_data.get("product_id")
        coupon = flow_data.get("coupon")
        address_id = flow_data.get("address_id")

        # 如果当前没有商品详情，就根据商品编号补查一次。
        if (not product or not product.get("title")) and product_id:
            from database.connection import get_db_context
            from services.product_service import ProductService

            async with get_db_context() as db:
                product_service = ProductService(db)
                product_data = await product_service.get_product(product_id)
                if product_data:
                    product = {
                        "id": product_data.get("id"),
                        "title": product_data.get("title"),
                        "price": product_data.get("price", 0)
                    }

        final_price = flow_data.get("final_price", product.get("price", 0))
        
        if not address_id:
            state["response"] = "请选择收货地址"
            return state
        
        from database.connection import get_db_context
        from sqlalchemy import select
        from database.models import Address
        
        async with get_db_context() as db:
            stmt = select(Address).where(Address.id == address_id)
            result = await db.execute(stmt)
            address = result.scalar_one_or_none()
            
            if not address:
                state["response"] = "地址不存在"
                return state
            
            address_info = {
                "id": address.id,
                "contact": address.contact,
                "phone": address.phone,
                "full_address": f"{address.province}{address.city}{address.district}{address.detail}"
            }
        
        state["purchase_flow"] = {
            **flow_data,
            "address": address_info,
            "step": "order_confirm"
        }
        
        state["response"] = f"""📋 订单确认

商品：{product.get('title')} × 1
原价：¥{product.get('price')}
{"优惠券：" + coupon["name"] + "（-¥" + str(coupon["discount"]) + "）" + "\n" if coupon else ""}实付：¥{final_price}
收货地址：{address_info['contact']} | {address_info['phone']} | {address_info['full_address']}

请确认订单信息："""
        
        state["quick_actions"] = [
            {
                "type": "button",
                "label": "确认下单",
                "action": "purchase_flow",
                "data": {
                    "step": "payment",
                    "product_id": flow_data.get("product_id"),
                    "coupon_id": flow_data.get("coupon_id"),
                    "address_id": address_id,
                    "product": product,
                    "coupon": coupon,
                    "address": address_info,
                    "final_price": final_price
                },
                "icon": "✅"
            },
            {
                "type": "button",
                "label": "修改信息",
                "action": "purchase_flow",
                "data": {
                    "step": "start",
                    "product_id": flow_data.get("product_id")
                },
                "icon": "✏️"
            }
        ]
        
        return state
    
    async def handle_order_confirm(self, state: ConversationState, flow_data: dict):
        """步骤4: 订单确认（预留）"""
        return await self.handle_confirm_address(state, {**flow_data, "step": "confirm_address"})
    
    async def handle_payment(self, state: ConversationState, flow_data: dict):
        """步骤5: 支付"""
        product = flow_data.get("product", {})
        product_id = flow_data.get("product_id")
        coupon = flow_data.get("coupon")
        address = flow_data.get("address")
        address_id = flow_data.get("address_id")
        final_price = flow_data.get("final_price", 0)

        # 如果当前没有商品详情，就根据商品编号补查一次。
        if (not product or not product.get("id")) and product_id:
            from database.connection import get_db_context as _get_db
            from services.product_service import ProductService

            async with _get_db() as db:
                product_service = ProductService(db)
                product_data = await product_service.get_product(product_id)
                if product_data:
                    product = {
                        "id": product_data.get("id"),
                        "title": product_data.get("title"),
                        "price": product_data.get("price", 0)
                    }
                    if not final_price:
                        final_price = product.get("price", 0)

        # 如果当前没有地址详情，就根据地址编号补查一次。
        if (not address or not address.get("full_address")) and address_id:
            from database.connection import get_db_context as _get_db2
            from sqlalchemy import select
            from database.models import Address

            async with _get_db2() as db:
                stmt = select(Address).where(Address.id == address_id)
                result = await db.execute(stmt)
                addr = result.scalar_one_or_none()
                if addr:
                    address = {
                        "id": addr.id,
                        "contact": addr.contact,
                        "phone": addr.phone,
                        "full_address": f"{addr.province}{addr.city}{addr.district}{addr.detail}"
                    }
        
        from database.connection import get_db_context
        from services.order_service import OrderService
        import uuid
        
        async with get_db_context() as db:
            order_service = OrderService(db)
            
            order_result = await order_service.create_order(
                buyer_id=state.get("user_id"),
                product_ids=[product.get("id")]
            )
            
            if order_result.get("id"):
                order_no = order_result.get("order_no", f"ORD{uuid.uuid4().hex[:12].upper()}")
                order_id = order_result.get("id")
                
                state["purchase_flow"] = {
                    **flow_data,
                    "order_id": order_id,
                    "order_no": order_no,
                    "step": "payment_done"
                }
                
                state["response"] = f"""🎉 订单已创建！

订单号：{order_no}
商品：{product.get('title')}
实付金额：¥{final_price}
收货地址：{address.get('full_address') if address else '未设置'}

请选择支付方式："""
                
                state["quick_actions"] = [
                    {
                        "type": "button",
                        "label": "微信支付",
                        "action": "purchase_flow",
                        "data": {
                            "step": "payment_done",
                            "order_id": order_id,
                            "order_no": order_no,
                            "payment_method": "wechat",
                            "final_price": final_price
                        },
                        "icon": "💚"
                    },
                    {
                        "type": "button",
                        "label": "支付宝",
                        "action": "purchase_flow",
                        "data": {
                            "step": "payment_done",
                            "order_id": order_id,
                            "order_no": order_no,
                            "payment_method": "alipay",
                            "final_price": final_price
                        },
                        "icon": "🔵"
                    }
                ]
            else:
                state["response"] = "订单创建失败，请重试"
        
        return state
    
    async def handle_payment_done(self, state: ConversationState, flow_data: dict):
        """步骤6: 支付完成 - 显示支付密码输入框"""
        order_no = flow_data.get("order_no", "")
        order_id = flow_data.get("order_id", "")
        payment_method = flow_data.get("payment_method", "wechat")
        final_price = flow_data.get("final_price", 0)
        
        method_name = "微信支付" if payment_method == "wechat" else "支付宝"
        
        state["purchase_flow"] = {
            **flow_data,
            "step": "payment_password"
        }
        
        state["response"] = f"""💳 {method_name}

订单号：{order_no}
支付金额：¥{final_price}

请输入6位数字支付密码完成支付："""
        
        # 通过特殊的动作类型触发前端支付弹窗。
        state["quick_actions"] = [
            {
                "type": "payment_password",
                "label": f"使用{method_name}支付",
                "action": "payment_password",
                "data": {
                    "order_id": order_id,
                    "order_no": order_no,
                    "payment_method": payment_method,
                    "amount": final_price
                },
                "icon": "🔐"
            }
        ]
        
        return state
    
    async def handle_payment_success(self, state: ConversationState, flow_data: dict):
        """步骤7: 支付成功 - 完成订单支付"""
        order_no = flow_data.get("order_no", "")
        order_id = flow_data.get("order_id", "")
        payment_method = flow_data.get("payment_method", "wechat")
        
        method_name = "微信支付" if payment_method == "wechat" else "支付宝"
        
        # 更新订单状态为已支付
        from database.connection import get_db_context
        from services.order_service import OrderService
        
        try:
            async with get_db_context() as db:
                order_service = OrderService(db)
                # 更新订单状态为已支付
                await order_service.update_order_status(
                    order_id=order_id,
                    status="paid"
                )
        except Exception as e:
            logger.error(f"更新订单状态失败: {e}")
        
        state["purchase_flow"] = None  # 清空购买流程
        
        state["response"] = f"""🎉 支付成功！

订单号：{order_no}
支付方式：{method_name}
支付时间：{__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

您的订单已支付成功，我们将尽快为您安排发货。
您可以在"我的订单"中查看订单详情。"""
        
        state["quick_actions"] = [
            {
                "type": "button",
                "label": "查看我的订单",
                "action": "navigate",
                "data": {
                    "path": "/orders"
                },
                "icon": "📦"
            },
            {
                "type": "button",
                "label": "继续购物",
                "action": "navigate",
                "data": {
                    "path": "/products"
                },
                "icon": "🛒"
            }
        ]
        
        return state
