"""
商品知识库同步服务
将商品信息同步到 Chroma 向量数据库，用于 AI 推荐和咨询
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Product, Review
from .knowledge_retriever import knowledge_retriever
import json


class ProductKnowledgeSync:
    """商品知识库同步类"""
    
    async def sync_product_to_knowledge(
        self,
        db: AsyncSession,
        product_id: str
    ) -> bool:
        """
        将单个商品同步到知识库
        
        Args:
            db: 数据库会话
            product_id: 商品ID
            
        Returns:
            是否成功
        """
        if not knowledge_retriever.available:
            return False
        
        # 获取商品信息
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product or product.status != "published":
            return False
        
        # 获取商品评价
        reviews_result = await db.execute(
            select(Review)
            .where(Review.product_id == product_id)
            .order_by(Review.rating.desc())
            .limit(5)
        )
        reviews = reviews_result.scalars().all()
        
        # 构建商品文档内容
        content_parts = [
            f"商品名称：{product.title}",
            f"商品描述：{product.description}",
            f"价格：¥{product.price}",
            f"技术栈：{', '.join(product.tech_stack or [])}",
            f"难度：{product.difficulty}",
            f"评分：{product.rating}⭐",
            f"销量：{product.sales_count}",
        ]
        
        if product.features:
            content_parts.append(f"特色功能：{', '.join(product.features)}")
        
        if product.deliverables:
            content_parts.append(f"交付内容：{', '.join(product.deliverables)}")
        
        # 添加评价摘要
        if reviews:
            review_texts = [f"用户评价：{r.comment}" for r in reviews if r.comment]
            if review_texts:
                content_parts.append("\n".join(review_texts[:3]))  # 只取前3条
        
        content = "\n".join(content_parts)
        
        # 准备文档数据
        document = {
            "id": f"product_{product.id}",
            "content": content,
            "metadata": {
                "product_id": product.id,
                "title": product.title,
                "price": float(product.price),
                "difficulty": product.difficulty,
                "rating": float(product.rating),
                "sales_count": product.sales_count,
                "tech_stack": json.dumps(product.tech_stack or [], ensure_ascii=False),
                "category_id": product.category_id,
                "seller_id": product.seller_id,
                "source": "product_catalog"
            }
        }
        
        # 添加到向量数据库
        await knowledge_retriever.add_documents([document], "product_catalog")
        
        return True
    
    async def sync_all_products(self, db: AsyncSession) -> Dict[str, Any]:
        """
        同步所有已发布的商品到知识库
        
        Args:
            db: 数据库会话
            
        Returns:
            同步结果统计
        """
        if not knowledge_retriever.available:
            return {"success": False, "message": "知识库不可用"}
        
        # 获取所有已发布的商品
        result = await db.execute(
            select(Product).where(Product.status == "published")
        )
        products = result.scalars().all()
        
        success_count = 0
        failed_count = 0
        
        for product in products:
            try:
                success = await self.sync_product_to_knowledge(db, product.id)
                if success:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"同步商品 {product.id} 失败：{e}")
                failed_count += 1
        
        return {
            "success": True,
            "total": len(products),
            "success_count": success_count,
            "failed_count": failed_count
        }
    
    async def remove_product_from_knowledge(
        self,
        product_id: str
    ) -> bool:
        """
        从知识库删除商品
        
        Args:
            product_id: 商品ID
            
        Returns:
            是否成功
        """
        if not knowledge_retriever.available:
            return False
        
        try:
            await knowledge_retriever.delete_document(
                f"product_{product_id}",
                "product_catalog"
            )
            return True
        except Exception as e:
            print(f"删除商品知识库失败：{e}")
            return False
    
    async def update_product_in_knowledge(
        self,
        db: AsyncSession,
        product_id: str
    ) -> bool:
        """
        更新知识库中的商品信息
        
        Args:
            db: 数据库会话
            product_id: 商品ID
            
        Returns:
            是否成功
        """
        # 先删除旧数据
        await self.remove_product_from_knowledge(product_id)
        
        # 重新添加
        return await self.sync_product_to_knowledge(db, product_id)


# 全局实例
product_knowledge_sync = ProductKnowledgeSync()
