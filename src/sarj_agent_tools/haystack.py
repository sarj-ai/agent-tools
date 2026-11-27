"""Haystack Tool/Toolset integration without credential serialization."""

from __future__ import annotations

from typing import Any

from haystack.core.errors import SerializationError
from haystack.tools import Tool, Toolset
from haystack.tools.errors import ToolInvocationError

from .client import SarjReadClient, SarjToolError, _bind
from .schemas import READ_SPECS


class _SarjTool(Tool):
    def invoke(self, **kwargs: Any) -> dict[str, Any]:
        message = "CONNECTION: The Sarj tool invocation failed."
        try:
            if self.function is not None:
                return self.function(**kwargs)
        except SarjToolError as error:
            message = str(error)
        except Exception:
            pass
        raise ToolInvocationError(message, tool_name=self.name)

    async def invoke_async(self, **kwargs: Any) -> dict[str, Any]:
        message = "CONNECTION: The Sarj tool invocation failed."
        try:
            if self.async_function is not None:
                return await self.async_function(**kwargs)
        except SarjToolError as error:
            message = str(error)
        except Exception:
            pass
        raise ToolInvocationError(message, tool_name=self.name)

    def to_dict(self) -> dict[str, Any]:
        raise SerializationError(
            "Recreate Sarj tools with an explicit credential; do not serialize keys."
        )


class SarjToolset(Toolset):
    """Four native Haystack tools, ready for Tool.invoke or Agent tools=[toolset]."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: SarjReadClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        if (api_key is None) == (client is None):
            raise SarjToolError("CONFIGURATION")
        self._client = (
            client if client is not None else SarjReadClient(api_key=api_key, timeout=timeout)
        )
        tools: list[Tool] = []
        for spec in READ_SPECS:
            function, coroutine = _bind(self._client, spec.operation)
            tools.append(
                _SarjTool(
                    name=spec.tool_name,
                    description=spec.description,
                    parameters=spec.input_model.model_json_schema(),
                    function=function,
                    async_function=coroutine,
                )
            )
        super().__init__(tools=tools)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SarjToolset:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def to_dict(self) -> dict[str, Any]:
        raise SerializationError(
            "Recreate SarjToolset with an explicit credential; keys are not serialized."
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SarjToolset:
        raise SerializationError("Construct SarjToolset with an explicit credential instead.")
