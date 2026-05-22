import httpx, asyncio

async def test():
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            "https://deepseek-api-resale-production.up.railway.app/v1/chat/completions",
            headers={
                "Authorization": "Bearer dsk_BgJMdsavB8gSrtyiudMBHxQxFmnMOrPtolW2ocbbZ-w",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-v4-flash",
                "messages": [{"role": "user", "content": "hi"}],
            },
        )
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("OK:", r.json()["choices"][0]["message"]["content"])
        else:
            print("Error:", r.text[:500])

asyncio.run(test())
