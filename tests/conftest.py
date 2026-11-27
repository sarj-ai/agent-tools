import os
import socket

import pytest

os.environ["HAYSTACK_TELEMETRY_ENABLED"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Tests must use synthetic HTTP transports, not live sockets.")

    monkeypatch.setattr(socket.socket, "connect", denied)
