"""
初始化数据库表
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from database.models import Base
from config import settings

async def init_db():
    """创建所有数据库表"""
    # 确保数据目录存在
    os.makedirs('./data', exist_ok=True)

    engine = create_async_engine(settings.database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print('✅ 数据库表创建成功')
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
