import asyncio
from database.connection import async_session
from services.product_service import ProductService

async def test():
    async with async_session() as db:
        service = ProductService(db)
        # Try to get the first product
        product = await service.get_product("dfab8bf9-3135-4abc-9e65-473b1304a513", increment_view=True)
        print(f"Product: {product}")

asyncio.run(test())
