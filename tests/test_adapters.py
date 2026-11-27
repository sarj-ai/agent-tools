import json
import pickle
import runpy

import pytest
from haystack.core.errors import SerializationError
from haystack.tools import Tool, Toolset
from haystack.tools.errors import ToolInvocationError
from langchain_core.tools import BaseToolkit, StructuredTool

from sarj_agent_tools import SarjToolError
from sarj_agent_tools.haystack import SarjToolset
from sarj_agent_tools.langchain import SarjToolkit
from sarj_agent_tools.schemas import READ_SPECS

from .fixtures import CALL_ID, KEY, PAYLOAD, Fixture


def tools_for(framework, client):
    if framework == "langchain":
        toolkit = SarjToolkit(client=client)
        assert isinstance(toolkit, BaseToolkit)
        result = toolkit.get_tools()
        assert all(isinstance(tool, StructuredTool) for tool in result)
        assert toolkit.model_dump() == {}
        return result
    toolset = SarjToolset(client=client)
    assert isinstance(toolset, Toolset)
    assert all(isinstance(tool, Tool) for tool in toolset)
    return list(toolset)


def invoke(framework, tool, arguments):
    return tool.invoke(arguments) if framework == "langchain" else tool.invoke(**arguments)


async def ainvoke(framework, tool, arguments):
    if framework == "langchain":
        return await tool.ainvoke(arguments)
    return await tool.invoke_async(**arguments)


@pytest.mark.parametrize("framework", ["langchain", "haystack"])
def test_actual_sync_tools(framework):
    fixture = Fixture()
    with fixture.client() as client:
        tools = tools_for(framework, client)
        assert [tool.name for tool in tools] == [spec.tool_name for spec in READ_SPECS]
        for index, tool in enumerate(tools):
            arguments = {"limit": 2, "status": "completed"} if index == 0 else {"call_id": CALL_ID}
            assert invoke(framework, tool, arguments) == PAYLOAD
            schema = tool.args_schema if framework == "langchain" else tool.parameters
            assert schema["additionalProperties"] is False
        assert [r.url.path for r in fixture.requests] == [
            "/api/v1/calls",
            f"/api/v1/calls/{CALL_ID}",
            f"/api/v1/calls/{CALL_ID}/transcript",
            f"/api/v1/calls/{CALL_ID}/analysis",
        ]
        assert all(r.method == "GET" for r in fixture.requests)
        assert all(r.url.host == "platform-api.sarj.ai" for r in fixture.requests)
        assert all(r.headers["authorization"] == f"Bearer {KEY}" for r in fixture.requests)
        assert all(r.headers["cache-control"] == "no-store" for r in fixture.requests)
        assert len(fixture.transports) == 4
        assert all(t.closed for t in fixture.transports)


@pytest.mark.parametrize("framework", ["langchain", "haystack"])
async def test_native_async_tools(framework):
    fixture = Fixture()
    client = fixture.client()
    for index, tool in enumerate(tools_for(framework, client)):
        assert await ainvoke(framework, tool, {} if index == 0 else {"call_id": CALL_ID}) == PAYLOAD
    assert all(t.closed for t in fixture.transports)


@pytest.mark.parametrize("framework", ["langchain", "haystack"])
@pytest.mark.parametrize(
    "arguments",
    [
        {"limit": 0},
        {"limit": 101},
        {"limit": True},
        {"limit": "2"},
        {"cursor": "x" * 129},
        {"status": "invented"},
        {"organization_id": "bad"},
        {"scenario_id": "bad"},
        {"created_from": "2026-11-01T00:00:00"},
        {"created_to": "2026-02-31T00:00:00Z"},
        {"operation": "create_call"},
        {"api_key": "synthetic-should-not-echo"},
    ],
)
def test_strict_native_adapter_inputs(framework, arguments):
    fixture = Fixture()
    tool = tools_for(framework, fixture.client())[0]
    error_class = SarjToolError if framework == "langchain" else ToolInvocationError
    with pytest.raises(error_class, match="INVALID_INPUT") as caught:
        invoke(framework, tool, arguments)
    assert "synthetic-should-not-echo" not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert fixture.requests == []


@pytest.mark.parametrize("framework", ["langchain", "haystack"])
@pytest.mark.parametrize("call_id", ["../other", "https://other.invalid", "a/b", "bad?query=1"])
def test_path_inputs_cannot_escape_calls(framework, call_id):
    fixture = Fixture()
    tool = tools_for(framework, fixture.client())[1]
    with pytest.raises(Exception, match="INVALID_INPUT"):
        invoke(framework, tool, {"call_id": call_id})
    assert not fixture.requests


@pytest.mark.parametrize("framework", ["langchain", "haystack"])
@pytest.mark.parametrize(
    "status,code",
    [
        (401, "AUTHENTICATION"),
        (403, "AUTHORIZATION"),
        (404, "NOT_FOUND"),
        (429, "RATE_LIMITED"),
        (500, "HTTP_ERROR"),
    ],
)
def test_service_errors_are_sanitized_through_framework(framework, status, code):
    import httpx

    fixture = Fixture(lambda request: httpx.Response(status, text=f"private body: {KEY}"))
    tool = tools_for(framework, fixture.client())[0]
    with pytest.raises(Exception, match=code) as caught:
        invoke(framework, tool, {"cursor": "synthetic-private-cursor"})
    assert KEY not in str(caught.value)
    assert "private body" not in str(caught.value)
    assert "synthetic-private-cursor" not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert all(t.closed for t in fixture.transports)


def test_credential_serialization_and_representations():
    fixture = Fixture()
    client = fixture.client()
    toolkit = SarjToolkit(client=client)
    toolset = SarjToolset(client=client)
    assert KEY not in repr(client)
    assert KEY not in repr(toolkit)
    assert KEY not in repr(toolset)
    assert KEY not in toolkit.model_dump_json()
    with pytest.raises(TypeError, match="do not pickle"):
        pickle.dumps(client)
    for tool in toolkit.get_tools():
        assert KEY not in json.dumps(tool.to_json())
    with pytest.raises(SerializationError):
        toolset.to_dict()
    for tool in toolset:
        with pytest.raises(SerializationError):
            tool.to_dict()


def test_optional_frameworks_do_not_change_the_four_tool_contract():
    for adapter in [SarjToolkit, SarjToolset]:
        with pytest.raises(SarjToolError, match="CONFIGURATION"):
            adapter()
        with pytest.raises(SarjToolError, match="CONFIGURATION"):
            adapter(api_key=KEY, client=Fixture().client())


@pytest.mark.parametrize("framework", ["langchain", "haystack"])
def test_closed_adapter_prevents_more_requests(framework):
    fixture = Fixture()
    adapter = (
        SarjToolkit(client=fixture.client())
        if framework == "langchain"
        else SarjToolset(client=fixture.client())
    )
    tools = adapter.get_tools() if framework == "langchain" else list(adapter)
    adapter.close()
    adapter.close()
    with pytest.raises(Exception, match="CLOSED"):
        invoke(framework, tools[0], {})
    assert not fixture.requests


def test_haystack_pipeline_example_runs(capsys):
    runpy.run_path("examples/haystack_pipeline.py", run_name="__main__")
    assert "synthetic call read completed" in capsys.readouterr().out
