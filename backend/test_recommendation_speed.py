"""
测试商品推荐速度
"""
import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai.workflow import AIWorkflow


async def test_speed():
    """测试推荐速度"""
    print("=" * 80)
    print("测试商品推荐速度")
    print("=" * 80)
    
    workflow = AIWorkflow()
    
    message = "推荐一个商品"
    
    print(f"\n用户消息: {message}")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        result = await workflow.process_message(
            user_id="test_user",
            session_id="test_session_speed",
            message=message
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"\n✅ 成功")
        print(f"⏱️  总耗时: {elapsed:.2f}秒")
        print(f"意图: {result.get('intent', 'N/A')}")
        print(f"回复长度: {len(result['response'])} 字符")
        
        if elapsed > 10:
            print(f"\n⚠️  警告: 耗时超过10秒！")
        elif elapsed > 5:
            print(f"\n⚠️  注意: 耗时超过5秒")
        else:
            print(f"\n✅ 性能良好")
        
    except Exception as e:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"\n❌ 失败: {e}")
        print(f"⏱️  失败前耗时: {elapsed:.2f}秒")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_speed())
