"""A real Haystack Pipeline using a native Sarj tool and synthetic HTTP data."""

import httpx
from haystack import Pipeline, component
from haystack.tools import Tool

from sarj_agent_tools import SarjReadClient
from sarj_agent_tools.haystack import SarjToolset


@component
class ReadCall:
    def __init__(self, tool: Tool) -> None:
        self._tool = tool

    @component.output_types(result=dict)
    def run(self, call_id: str) -> dict:
        return {"result": self._tool.invoke(call_id=call_id)}


def main() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.host == "platform-api.sarj.ai"
        return httpx.Response(200, json={"synthetic": True})

    with SarjReadClient(
        api_key="synthetic-pipeline-key",
        transport_factory=lambda: httpx.MockTransport(handler),
    ) as client:
        tools = {tool.name: tool for tool in SarjToolset(client=client)}
        pipeline = Pipeline()
        pipeline.add_component("read", ReadCall(tools["sarj_get_call"]))
        result = pipeline.run({"read": {"call_id": "11111111-1111-4111-8111-111111111111"}})
        assert result["read"]["result"] == {"synthetic": True}
        print("Haystack Pipeline: synthetic call read completed.")


if __name__ == "__main__":
    main()
