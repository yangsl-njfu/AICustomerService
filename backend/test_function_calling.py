"""
Function Calling功能测试脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.function_tools import function_tool_manager


async def test_query_order():
    """测试订单查询工具"""
    print("\n=== 测试订单查询工具 ===")
    try:
        result = await function_tool_manager.execute(
            "query_order",
            order_no="ORD20240207123456"
        )
        print(f"✓ 订单查询成功")
        print(f"  结果: {result}")
    except Exception as e:
        print(f"✗ 订单查询失败: {e}")


async def test_search_products():
    """测试商品搜索工具"""
    print("\n=== 测试商品搜索工具 ===")
    try:
        result = await function_tool_manager.execute(
            "search_products",
            keyword="Vue",
            max_price=500
        )
        print(f"✓ 商品搜索成功")
        print(f"  找到 {result.get('total', 0)} 个商品")
        if result.get('products'):
            for i, p in enumerate(result['products'][:3], 1):
                print(f"  {i}. {p['title']} - ¥{p['price']}")
    except Exception as e:
        print(f"✗ 商品搜索失败: {e}")


async def test_check_inventory():
    """测试库存检查工具"""
    print("\n=== 测试库存检查工具 ===")
    try:
        result = await function_tool_manager.execute(
            "check_inventory",
            product_id="test-product-id"
        )
        print(f"✓ 库存检查成功")
        print(f"  结果: {result}")
    except Exception as e:
        print(f"✗ 库存检查失败: {e}")


async def test_calculate_price():
    """测试价格计算工具"""
    print("\n=== 测试价格计算工具 ===")
    try:
        result = await function_tool_manager.execute(
            "calculate_price",
            product_ids=["product1", "product2"]
        )
        print(f"✓ 价格计算成功")
        print(f"  结果: {result}")
    except Exception as e:
        print(f"✗ 价格计算失败: {e}")


async def test_tools_schema():
    """测试工具schema获取"""
    print("\n=== 测试工具Schema ===")
    try:
        schemas = function_tool_manager.get_tools_schema()
        print(f"✓ 获取工具Schema成功")
        print(f"  共注册 {len(schemas)} 个工具:")
        for schema in schemas:
            print(f"  - {schema['name']}: {schema['description']}")
    except Exception as e:
        print(f"✗ 获取工具Schema失败: {e}")


async def main():
    """主测试函数"""
    print("=" * 60)
    print("Function Calling 功能测试")
    print("=" * 60)
    
    # 测试工具Schema
    await test_tools_schema()
    
    # 测试各个工具（这些测试可能会失败，因为需要数据库连接）
    print("\n注意: 以下测试需要数据库连接，可能会失败")
    print("-" * 60)
    
    await test_search_products()
    await test_query_order()
    await test_check_inventory()
    await test_calculate_price()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
