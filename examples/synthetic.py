"""Run both native framework adapters using synthetic HTTP responses only."""

import asyncio

import httpx

from sarj_agent_tools import SarjReadClient
from sarj_agent_tools.haystack import SarjToolset
from sarj_agent_tools.langchain import SarjToolkit

CALL_ID = "11111111-1111-4111-8111-111111111111"


def handler(request: httpx.Request) -> httpx.Response:
    assert request.method == "GET"
    assert request.url.host == "platform-api.sarj.ai"
    assert request.headers["authorization"] == "Bearer synthetic-example-key"
    return httpx.Response(200, json={"synthetic": True, "data": {"pending": None}})


async def main() -> None:
    async with SarjReadClient(
        api_key="synthetic-example-key",
        transport_factory=lambda: httpx.MockTransport(handler),
    ) as client:
        langchain = SarjToolkit(client=client).get_tools()
        haystack = SarjToolset(client=client)
        for index, tool in enumerate(langchain):
            result = await tool.ainvoke({} if index == 0 else {"call_id": CALL_ID})
            assert result["synthetic"]
        for index, tool in enumerate(haystack):
            result = await tool.invoke_async(**({} if index == 0 else {"call_id": CALL_ID}))
            assert result["synthetic"]
        print("LangChain: four reads; Haystack: four reads. Synthetic data only.")


if __name__ == "__main__":
    asyncio.run(main())
