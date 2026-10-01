import asyncio

import httpx

from marketpulse.async_http_client import AsyncResilientClient


def test_respects_max_concurrency():
    state = {"in_flight": 0, "max": 0}

    async def handler(request):
        state["in_flight"] += 1
        state["max"] = max(state["max"], state["in_flight"])
        await asyncio.sleep(0.01)
        state["in_flight"] -= 1
        return httpx.Response(200)

    async def main():
        async with AsyncResilientClient(
            "https://example.test",
            max_concurrency=3,
            min_interval=0,
            transport=httpx.MockTransport(handler),
        ) as client:
            await asyncio.gather(*(client.get("/x") for _ in range(20)))

    asyncio.run(main())
    assert state["max"] == 3