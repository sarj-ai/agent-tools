"""LangChain BaseToolkit and StructuredTool integration."""

from __future__ import annotations

from langchain_core.tools import BaseTool, BaseToolkit, StructuredTool
from pydantic import PrivateAttr

from .client import SarjReadClient, SarjToolError, _bind
from .schemas import READ_SPECS


class SarjToolkit(BaseToolkit):
    """Provide exactly four Sarj call reads through LangChain's standard toolkit API."""

    _client: SarjReadClient = PrivateAttr()

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: SarjReadClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        super().__init__()
        if (api_key is None) == (client is None):
            raise SarjToolError("CONFIGURATION")
        self._client = (
            client if client is not None else SarjReadClient(api_key=api_key, timeout=timeout)
        )

    def get_tools(self) -> list[BaseTool]:
        tools: list[BaseTool] = []
        for spec in READ_SPECS:
            function, coroutine = _bind(self._client, spec.operation)
            tools.append(
                StructuredTool.from_function(
                    func=function,
                    coroutine=coroutine,
                    name=spec.tool_name,
                    description=spec.description,
                    args_schema=spec.input_model.model_json_schema(),
                    infer_schema=False,
                )
            )
        return tools

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SarjToolkit:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
