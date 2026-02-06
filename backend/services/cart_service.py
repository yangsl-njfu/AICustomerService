"""
购物车服务模块
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from database.models import CartItem, Product, ProductStatus
import uuid


class CartService:
    """购物车服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_to_cart(self, user_id: str, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """添加商品到购物车"""
        # 检查商品是否存在且已发布
        result = await self.db.execute(
            select(Product).where(
                and_(
                    Product.id == product_id,
                    Product.status == ProductStatus.PUBLISHED
                )
            )
        )
        product = result.scalar_one_or_none()

        if not product:
            raise ValueError("商品不存在或未发布")

        # 检查是否已在购物车
        result = await self.db.execute(
            select(CartItem).where(
                and_(
                    CartItem.user_id == user_id,
                    CartItem.product_id == product_id
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 更新数量
            existing.quantity += quantity
            await self.db.commit()
            await self.db.refresh(existing)
            return {"message": "商品数量已更新", "cart_item_id": existing.id}

        # 添加到购物车
        cart_item = CartItem(
            id=str(uuid.uuid4()),
            user_id=user_id,
            product_id=product_id,
            quantity=quantity
        )

        self.db.add(cart_item)
        await self.db.commit()
        await self.db.refresh(cart_item)

        return {"message": "添加成功", "cart_item_id": cart_item.id}
    
    async def remove_from_cart(self, user_id: str, product_id: str) -> bool:
        """从购物车删除商品"""
        result = await self.db.execute(
            select(CartItem).where(
                and_(
                    CartItem.user_id == user_id,
                    CartItem.product_id == product_id
                )
            )
        )
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            return False
        
        await self.db.delete(cart_item)
        await self.db.commit()
        
        return True
    
    async def get_cart(self, user_id: str) -> Dict[str, Any]:
        """获取购物车"""
        result = await self.db.execute(
            select(CartItem)
            .options(
                joinedload(CartItem.product).joinedload(Product.seller),
                joinedload(CartItem.product).joinedload(Product.category)
            )
            .where(CartItem.user_id == user_id)
            .order_by(CartItem.created_at.desc())
        )
        cart_items = result.scalars().all()
        
        items = []
        total_amount = 0
        
        for cart_item in cart_items:
            product = cart_item.product
            
            # 只包含已发布的商品
            if product.status != ProductStatus.PUBLISHED:
                continue
            
            item_data = {
                "id": cart_item.id,
                "user_id": cart_item.user_id,
                "product_id": product.id,
                "quantity": cart_item.quantity,
                "created_at": cart_item.created_at.isoformat() if cart_item.created_at else None,
                "product": {
                    "id": product.id,
                    "title": product.title,
                    "price": product.price,  # 保持分为单位
                    "cover_image": product.cover_image,
                    "difficulty": product.difficulty,
                    "status": product.status.value if product.status else None,
                    "seller": {
                        "id": product.seller.id,
                        "username": product.seller.username
                    } if product.seller else None
                }
            }

            items.append(item_data)
            total_amount += product.price * cart_item.quantity
        
        return {
            "items": items,
            "total_amount": total_amount,  # 保持分为单位
            "total_items": sum(item["quantity"] for item in items)
        }

    async def update_quantity(self, user_id: str, product_id: str, quantity: int) -> Optional[Dict[str, Any]]:
        """更新购物车商品数量"""
        if quantity <= 0:
            # 如果数量小于等于0，删除该商品
            return await self.remove_from_cart(user_id, product_id)

        result = await self.db.execute(
            select(CartItem).where(
                and_(
                    CartItem.user_id == user_id,
                    CartItem.product_id == product_id
                )
            )
        )
        cart_item = result.scalar_one_or_none()

        if not cart_item:
            return None

        cart_item.quantity = quantity
        await self.db.commit()
        await self.db.refresh(cart_item)

        return {"message": "数量已更新", "cart_item_id": cart_item.id, "quantity": cart_item.quantity}

    async def clear_cart(self, user_id: str) -> bool:
        """清空购物车"""
        result = await self.db.execute(
            select(CartItem).where(CartItem.user_id == user_id)
        )
        cart_items = result.scalars().all()
        
        for item in cart_items:
            await self.db.delete(item)
        
        await self.db.commit()
        
        return True
    
    async def get_cart_count(self, user_id: str) -> int:
        """获取购物车商品数量"""
        result = await self.db.execute(
            select(CartItem).where(CartItem.user_id == user_id)
        )
        cart_items = result.scalars().all()
        
        return len(cart_items)
