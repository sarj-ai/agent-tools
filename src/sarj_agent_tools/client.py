"""A fixed-route, request-scoped HTTP client. No framework import is required."""

from __future__ import annotations

import asyncio
import json
import math
import re
from collections.abc import Callable
from contextlib import suppress
from typing import Any

import httpx
from pydantic import SecretStr, ValidationError

from .schemas import READ_SPECS

BASE_URL = "https://platform-api.sarj.ai/api/v1"
_SPECS = {spec.operation: spec for spec in READ_SPECS}
_MESSAGES = {
    "CONFIGURATION": "Supply one raw Sarj API key and valid timeout/response limits.",
    "INVALID_INPUT": "Inputs do not match this read tool's schema.",
    "AUTHENTICATION": "Sarj authentication failed. Check the key and its expiry.",
    "AUTHORIZATION": (
        "Sarj denied access. Check calls:read, organization membership and pilot access."
    ),
    "NOT_FOUND": "The requested call or read endpoint was not available to this credential.",
    "RATE_LIMITED": "Sarj rate-limited the read. Retry according to your application's policy.",
    "HTTP_ERROR": "Sarj returned an unsuccessful HTTP response.",
    "PROTOCOL": "Sarj returned an invalid JSON response.",
    "CONNECTION": "The Sarj connection failed.",
    "TIMEOUT": "The Sarj read deadline expired.",
    "RESPONSE_TOO_LARGE": "The Sarj response exceeded the configured byte limit.",
    "CLOSED": "This Sarj client is closed.",
    "ASYNC_REQUIRED": "Use the async tool interface inside a running event loop.",
}


class SarjToolError(RuntimeError):
    """Safe error metadata; never retains a request, body, input or upstream cause."""

    def __init__(self, code: str, *, status: int | None = None) -> None:
        super().__init__(f"{code}: {_MESSAGES[code]}")
        self.code = code
        self.status = status


class SarjReadClient:
    """One credential, four GET operations, and a fresh owned HTTP client per invocation."""

    def __init__(
        self,
        *,
        api_key: str,
        timeout: float = 30.0,
        max_response_bytes: int = 16 * 1024 * 1024,
        transport_factory: Callable[[], httpx.AsyncBaseTransport] | None = None,
    ) -> None:
        if (
            not isinstance(api_key, str)
            or re.fullmatch(r"[A-Za-z0-9\-._~+/]+=*", api_key) is None
            or isinstance(timeout, bool)
            or not isinstance(timeout, (float, int))
            or not math.isfinite(timeout)
            or not 0 < timeout <= 300
            or isinstance(max_response_bytes, bool)
            or not isinstance(max_response_bytes, int)
            or not 1 <= max_response_bytes <= 64 * 1024 * 1024
        ):
            raise SarjToolError("CONFIGURATION")
        self._key = SecretStr(api_key)
        self._timeout = float(timeout)
        self._max_response_bytes = max_response_bytes
        self._transport_factory = transport_factory
        self._closed = False

    def __repr__(self) -> str:
        return f"SarjReadClient(timeout={self._timeout}, closed={self._closed})"

    def __getstate__(self) -> object:
        raise TypeError("Recreate SarjReadClient with an explicit credential; do not pickle keys.")

    def __enter__(self) -> SarjReadClient:
        if self._closed:
            raise SarjToolError("CLOSED")
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    async def __aenter__(self) -> SarjReadClient:
        return self.__enter__()

    async def __aexit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Prevent new reads. In-flight requests retain their own deadline and cleanup."""
        self._closed = True

    def _sync(self, operation: str, arguments: dict[str, Any]) -> dict[str, Any]:
        running = False
        try:
            asyncio.get_running_loop()
            running = True
        except RuntimeError:
            pass
        if running:
            raise SarjToolError("ASYNC_REQUIRED")
        return asyncio.run(self._async(operation, arguments))

    async def _async(self, operation: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self._closed:
            raise SarjToolError("CLOSED")
        if operation not in _SPECS:
            raise SarjToolError("INVALID_INPUT")
        spec = _SPECS[operation]
        parsed = None
        with suppress(ValidationError):
            parsed = spec.input_model.model_validate(arguments)
        if parsed is None:
            raise SarjToolError("INVALID_INPUT")
        values = parsed.model_dump(exclude_none=True)
        if spec.suffix is None:
            path, query = "/calls", values
        else:
            path, query = f"/calls/{values['call_id']}{spec.suffix}", {}

        error: SarjToolError | None = None
        result: dict[str, Any] | None = None
        try:
            async with asyncio.timeout(self._timeout):
                transport = self._transport_factory() if self._transport_factory else None
                async with (
                    httpx.AsyncClient(
                        transport=transport,
                        timeout=self._timeout,
                        follow_redirects=False,
                        trust_env=False,
                        headers={
                            "Authorization": f"Bearer {self._key.get_secret_value()}",
                            "Accept": "application/json",
                            "Cache-Control": "no-store",
                        },
                    ) as client,
                    client.stream("GET", BASE_URL + path, params=query) as response,
                ):
                    if response.status_code != 200:
                        code = {
                            401: "AUTHENTICATION",
                            403: "AUTHORIZATION",
                            404: "NOT_FOUND",
                            429: "RATE_LIMITED",
                        }.get(response.status_code, "HTTP_ERROR")
                        error = SarjToolError(code, status=response.status_code)
                    else:
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            if len(body) + len(chunk) > self._max_response_bytes:
                                error = SarjToolError("RESPONSE_TOO_LARGE")
                                break
                            body.extend(chunk)
                        if error is None:
                            value = json.loads(body, parse_constant=_reject_json_constant)
                            if isinstance(value, dict):
                                result = value
                            else:
                                error = SarjToolError("PROTOCOL")
        except (TimeoutError, httpx.TimeoutException):
            error = SarjToolError("TIMEOUT")
        except httpx.HTTPError:
            error = SarjToolError("CONNECTION")
        except (ValueError, UnicodeError):
            error = SarjToolError("PROTOCOL")
        except Exception:
            error = SarjToolError("CONNECTION")
        if error is not None:
            raise error
        if result is None:
            raise SarjToolError("PROTOCOL")
        return result

    def list_calls(self, **filters: Any) -> dict[str, Any]:
        return self._sync("list_calls", filters)

    def get_call(self, *, call_id: str) -> dict[str, Any]:
        return self._sync("get_call", {"call_id": call_id})

    def get_call_transcript(self, *, call_id: str) -> dict[str, Any]:
        return self._sync("get_call_transcript", {"call_id": call_id})

    def get_call_analysis(self, *, call_id: str) -> dict[str, Any]:
        return self._sync("get_call_analysis", {"call_id": call_id})

    async def alist_calls(self, **filters: Any) -> dict[str, Any]:
        return await self._async("list_calls", filters)

    async def aget_call(self, *, call_id: str) -> dict[str, Any]:
        return await self._async("get_call", {"call_id": call_id})

    async def aget_call_transcript(self, *, call_id: str) -> dict[str, Any]:
        return await self._async("get_call_transcript", {"call_id": call_id})

    async def aget_call_analysis(self, *, call_id: str) -> dict[str, Any]:
        return await self._async("get_call_analysis", {"call_id": call_id})


def _reject_json_constant(_: str) -> None:
    raise ValueError("Invalid JSON constant.")


def _bind(client: SarjReadClient, operation: str) -> tuple[Callable[..., Any], Callable[..., Any]]:
    def invoke(**arguments: Any) -> dict[str, Any]:
        return client._sync(operation, arguments)

    async def ainvoke(**arguments: Any) -> dict[str, Any]:
        return await client._async(operation, arguments)

    return invoke, ainvoke
