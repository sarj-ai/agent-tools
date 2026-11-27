import asyncio

import httpx
import pytest

from sarj_agent_tools import SarjReadClient, SarjToolError

from .fixtures import CALL_ID, KEY, PAYLOAD, Fixture


@pytest.mark.parametrize("api_key", ["", "Bearer synthetic-key", "synthetic\r\nheader", None])
def test_invalid_credentials(api_key):
    with pytest.raises(SarjToolError, match="CONFIGURATION"):
        SarjReadClient(api_key=api_key)


def test_no_environment_auth_default(monkeypatch):
    monkeypatch.setenv("SARJ_API_KEY", KEY)
    with pytest.raises(TypeError):
        SarjReadClient()


@pytest.mark.parametrize(
    "kwargs",
    [{"timeout": 0}, {"timeout": float("inf")}, {"timeout": True}, {"max_response_bytes": 0}],
)
def test_bounded_configuration(kwargs):
    with pytest.raises(SarjToolError, match="CONFIGURATION"):
        SarjReadClient(api_key=KEY, **kwargs)


def test_query_filters_and_defaults():
    fixture = Fixture()
    client = fixture.client()
    result = client.list_calls(
        scenario_id=CALL_ID,
        organization_id=CALL_ID,
        status="completed",
        cursor="synthetic+page",
        created_from="2026-11-01T00:00:00Z",
        created_to="2026-12-01T01:00:00+01:00",
    )
    assert result == PAYLOAD
    query = dict(fixture.requests[0].url.params)
    assert query["limit"] == "20"
    assert query["cursor"] == "synthetic+page"
    assert query["organization_id"] == CALL_ID
    assert query["created_to"] == "2026-12-01T01:00:00+01:00"
    client.list_calls(scenario_id=None, status=None, cursor=None)
    assert dict(fixture.requests[1].url.params) == {"limit": "20"}


async def test_user_credentials_and_clients_are_isolated():
    fixture = Fixture()
    await asyncio.gather(
        *[fixture.client(key=f"synthetic-user-{i}").alist_calls(cursor=str(i)) for i in range(3)]
    )
    for request in fixture.requests:
        assert (
            request.headers["authorization"]
            == f"Bearer synthetic-user-{request.url.params['cursor']}"
        )
    assert all(t.closed for t in fixture.transports)


@pytest.mark.parametrize("body", ["not json", "[]", "null", '{"number": NaN}', b"\xff"])
def test_protocol_errors_do_not_retain_bodies(body):
    fixture = Fixture(lambda request: httpx.Response(200, content=body))
    with pytest.raises(SarjToolError, match="PROTOCOL") as caught:
        fixture.client().list_calls()
    assert caught.value.__context__ is None
    assert all(t.closed for t in fixture.transports)


def test_response_size_bound_and_cleanup():
    fixture = Fixture(lambda request: httpx.Response(200, text='{"value":"' + "x" * 50 + '"}'))
    with pytest.raises(SarjToolError, match="RESPONSE_TOO_LARGE"):
        fixture.client(max_response_bytes=20).list_calls()
    assert all(t.closed for t in fixture.transports)


def test_redirect_is_not_followed():
    fixture = Fixture(
        lambda request: httpx.Response(307, headers={"location": "https://other.invalid"})
    )
    with pytest.raises(SarjToolError, match="HTTP_ERROR") as caught:
        fixture.client().list_calls()
    assert caught.value.status == 307
    assert len(fixture.requests) == 1
    assert fixture.requests[0].url.host == "platform-api.sarj.ai"


async def test_overall_deadline_and_cleanup():
    async def slow(request):
        await asyncio.sleep(1)
        return httpx.Response(200, json=PAYLOAD)

    fixture = Fixture(slow)
    with pytest.raises(SarjToolError, match="TIMEOUT"):
        await fixture.client(timeout=0.01).alist_calls()
    assert all(t.closed for t in fixture.transports)


async def test_cancellation_propagates_and_closes_transport():
    started = asyncio.Event()

    async def slow(request):
        started.set()
        await asyncio.sleep(10)
        return httpx.Response(200, json=PAYLOAD)

    fixture = Fixture(slow)
    task = asyncio.create_task(fixture.client().alist_calls())
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert all(t.closed for t in fixture.transports)


async def test_sync_interface_in_event_loop_is_explicit():
    fixture = Fixture()
    with pytest.raises(SarjToolError, match="ASYNC_REQUIRED"):
        fixture.client().list_calls()
    assert not fixture.requests


def test_transport_exception_is_sanitized(caplog):
    def error(request):
        raise httpx.ConnectError(f"private transport error {KEY}", request=request)

    fixture = Fixture(error)
    with pytest.raises(SarjToolError, match="CONNECTION") as caught:
        fixture.client().list_calls()
    assert KEY not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert KEY not in caplog.text
    assert all(t.closed for t in fixture.transports)
