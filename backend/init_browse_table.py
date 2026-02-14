"""
初始化浏览历史表
"""
import asyncio
from database.connection import get_db_context
from sqlalchemy import text


async def init_browse_table():
    """创建浏览历史表（不带外键约束）"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS user_browse_history (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        product_id VARCHAR(36) NOT NULL,
        view_duration INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_user_product_browse (user_id, product_id),
        INDEX idx_user (user_id),
        INDEX idx_product (product_id),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    async with get_db_context() as db:
        await db.execute(text(create_table_sql))
        await db.commit()
        print("✅ 浏览历史表创建成功!")


if __name__ == "__main__":
    asyncio.run(init_browse_table())
