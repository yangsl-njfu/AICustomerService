import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        resp = await client.post('http://localhost:8000/api/auth/register', json={
            'username': 'yangsl',
            'password': '123456'
        })
        print(f'Status: {resp.status_code}')
        print(f'Response: {resp.text}')

asyncio.run(test())
