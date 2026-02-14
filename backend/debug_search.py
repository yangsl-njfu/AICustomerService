import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

async def test():
    from services.ai.workflow import AIWorkflow
    from services.redis_cache import redis_cache

    await redis_cache.connect()
    workflow = AIWorkflow()
    
    user_id = "545cd010-0000-4669-8847-5d3078545d1b"
    session_id = "test_session_001"
    message = "推荐一个python的商品"
    
    state = await workflow.prepare_intent(user_id, session_id, message)
    print(f"意图: {state.get('intent')}")
    
    state = await workflow.generate_response(state)
    print(f"工具: {state.get('tool_used')}")
    print(f"tool_result: {state.get('tool_result')}")
    print(f"响应: {state.get('response', '')[:100]}")
    
    await redis_cache.disconnect()

asyncio.run(test())
