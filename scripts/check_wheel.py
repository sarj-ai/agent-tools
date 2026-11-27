"""Wheel installation and offline native invocation checks in three isolated consumers."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

CONSUMER = r"""
import asyncio
import importlib.util
import socket
import sys

import httpx
import sarj_agent_tools
from sarj_agent_tools import SarjReadClient

mode = sys.argv[1]
assert "site-packages" in sarj_agent_tools.__file__
assert "langchain_core" not in sys.modules
assert "haystack" not in sys.modules
if mode != "langchain":
    assert importlib.util.find_spec("langchain_core") is None
if mode != "haystack":
    assert importlib.util.find_spec("haystack") is None

def deny_network(*args, **kwargs):
    raise AssertionError("Packed consumers must use synthetic HTTP only.")

socket.socket.connect = deny_network
call_id = "11111111-1111-4111-8111-111111111111"
requests = []
transports = []

class Transport(httpx.MockTransport):
    async def aclose(self):
        self.closed = True
        await super().aclose()

def handler(request):
    assert request.method == "GET"
    assert request.url.host == "platform-api.sarj.ai"
    assert request.headers["authorization"] == "Bearer synthetic-packed-read-key"
    requests.append(request)
    return httpx.Response(200, json={"synthetic": True, "data": {"value": None}})

def factory():
    transport = Transport(handler)
    transport.closed = False
    transports.append(transport)
    return transport

with SarjReadClient(api_key="synthetic-packed-read-key", transport_factory=factory) as client:
    if mode == "base":
        methods = [client.list_calls, client.get_call, client.get_call_transcript,
                   client.get_call_analysis]
        for index, method in enumerate(methods):
            result = method(**({} if index == 0 else {"call_id": call_id}))
            assert result["synthetic"] is True and result["data"]["value"] is None
    else:
        if mode == "langchain":
            from langchain_core.tools import BaseToolkit, StructuredTool
            from sarj_agent_tools.langchain import SarjToolkit
            adapter = SarjToolkit(client=client)
            assert isinstance(adapter, BaseToolkit)
            tools = adapter.get_tools()
            assert all(isinstance(tool, StructuredTool) for tool in tools)
        else:
            from haystack.tools import Tool, Toolset
            from sarj_agent_tools.haystack import SarjToolset
            adapter = SarjToolset(client=client)
            assert isinstance(adapter, Toolset)
            tools = list(adapter)
            assert all(isinstance(tool, Tool) for tool in tools)
        assert [tool.name for tool in tools] == ["sarj_list_calls", "sarj_get_call",
            "sarj_get_call_transcript", "sarj_get_call_analysis"]
        for index, tool in enumerate(tools):
            arguments = {} if index == 0 else {"call_id": call_id}
            result = tool.invoke(arguments) if mode == "langchain" else tool.invoke(**arguments)
            assert result["synthetic"] is True and result["data"]["value"] is None
        async def run():
            for index, tool in enumerate(tools):
                arguments = {} if index == 0 else {"call_id": call_id}
                if mode == "langchain":
                    result = await tool.ainvoke(arguments)
                else:
                    result = await tool.invoke_async(**arguments)
                assert result["synthetic"] is True and result["data"]["value"] is None
        asyncio.run(run())
        adapter.close()
assert len(requests) == (4 if mode == "base" else 8)
assert all(transport.closed for transport in transports)
print(f"{mode}: installed wheel, isolated extra, {len(requests)} reads and cleanup passed")
"""


def main() -> None:
    wheel = Path(sys.argv[1]).resolve(strict=True)
    environment = os.environ | {
        "HAYSTACK_TELEMETRY_ENABLED": "false",
        "LANGSMITH_TRACING": "false",
        "LANGCHAIN_TRACING_V2": "false",
    }
    with tempfile.TemporaryDirectory(prefix="sarj-packed-consumers-") as temporary:
        for mode in ("base", "langchain", "haystack"):
            directory = Path(temporary) / mode
            subprocess.run(
                ["uv", "venv", "--no-project", "--python", sys.executable, str(directory)],
                check=True,
                timeout=120,
            )
            python = directory / "bin" / "python"
            package = str(wheel) + (f"[{mode}]" if mode != "base" else "")
            command = ["uv", "pip", "install", "--python", str(python), package]
            subprocess.run([*command, "--dry-run"], check=True, timeout=120)
            subprocess.run(command, check=True, timeout=120)
            subprocess.run(
                [str(python), "-I", "-c", CONSUMER, mode],
                check=True,
                timeout=120,
                env=environment,
                cwd=directory,
            )


if __name__ == "__main__":
    main()
