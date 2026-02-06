"""
测试商品推荐功能
"""
import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai.workflow import AIWorkflow


async def test_product_recommendation():
    """测试商品推荐"""
    print("=" * 60)
    print("测试商品推荐功能")
    print("=" * 60)
    
    workflow = AIWorkflow()
    
    # 测试用例
    test_messages = [
        "你能给我推荐一个商品吗",
        "我想要一个Vue的毕业设计",
        "有没有500元以内的Python项目",
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n【测试 {i}】")
        print(f"用户消息: {message}")
        print("-" * 60)
        
        try:
            result = await workflow.process_message(
                user_id="test_user",
                session_id=f"test_session_{i}",
                message=message
            )
            
            print(f"✅ 成功")
            print(f"回复: {result['response'][:200]}...")
            print(f"意图: {result.get('intent', 'N/A')}")
            print(f"使用的工具: {result.get('tool_used', 'N/A')}")
            
            if result.get('quick_actions'):
                print(f"快速操作: {len(result['quick_actions'])} 个")
                for action in result['quick_actions'][:3]:
                    print(f"  - {action.get('label', 'N/A')}")
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_product_recommendation())
