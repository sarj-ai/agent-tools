from __future__ import annotations

from collections.abc import Callable

import httpx

from sarj_agent_tools import SarjReadClient

CALL_ID = "11111111-1111-4111-8111-111111111111"
KEY = "synthetic-read-key"
PAYLOAD = {"synthetic": True, "data": {"pending_value": None, "items": []}}


class RecordingTransport(httpx.MockTransport):
    def __init__(self, handler):
        super().__init__(handler)
        self.closed = False

    async def aclose(self):
        self.closed = True


class Fixture:
    def __init__(self, handler: Callable | None = None):
        self.requests: list[httpx.Request] = []
        self.transports: list[RecordingTransport] = []
        self.handler = handler

    def transport(self):
        def handle(request):
            self.requests.append(request)
            return self.handler(request) if self.handler else httpx.Response(200, json=PAYLOAD)

        transport = RecordingTransport(handle)
        self.transports.append(transport)
        return transport

    def client(self, *, key=KEY, **kwargs):
        return SarjReadClient(api_key=key, transport_factory=self.transport, **kwargs)
