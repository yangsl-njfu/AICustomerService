"""
售后退款功能数据库迁移脚本
- 创建 refund_requests 表
- 为 orders.status 枚举添加 'refunded' 值
- 为 transactions.status 枚举添加 'refunded' 值
"""
import asyncio
from sqlalchemy import text
from database.connection import engine, Base


async def migrate():
    # 1. 创建缺失的表（refund_requests）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] refund_requests table created")

    # 2. 为 orders.status 枚举添加 'refunded'
    async with engine.begin() as conn:
        try:
            await conn.execute(text(
                "ALTER TABLE orders MODIFY COLUMN status "
                "ENUM('PENDING','PAID','DELIVERED','COMPLETED','CANCELLED','REFUNDED') "
                "DEFAULT 'PENDING'"
            ))
            print("[OK] orders.status updated")
        except Exception as e:
            print(f"[SKIP] orders.status: {e}")

    # 3. 为 transactions.status 枚举添加 'refunded'
    async with engine.begin() as conn:
        try:
            await conn.execute(text(
                "ALTER TABLE transactions MODIFY COLUMN status "
                "ENUM('PENDING','SUCCESS','FAILED','REFUNDED') "
                "DEFAULT 'PENDING'"
            ))
            print("[OK] transactions.status updated")
        except Exception as e:
            print(f"[SKIP] transactions.status: {e}")

    print("\nMigration done!")


if __name__ == "__main__":
    asyncio.run(migrate())
