# SarjToolkit for LangChain

Install `pip install 'sarj-agent-tools[langchain]'`. Use Python 3.11+ and a Sarj organization API key with only `calls:read`. API credential creation requires an eligible account role; organization/pilot permissions may restrict reads.

```python
from sarj_agent_tools import SarjReadClient
from sarj_agent_tools.langchain import SarjToolkit

async def review_calls(api_key: str) -> dict:
    async with SarjReadClient(api_key=api_key) as client:
        tools = {tool.name: tool for tool in SarjToolkit(client=client).get_tools()}
        return await tools["sarj_list_calls"].ainvoke({"limit": 3})
```

The toolkit implements LangChain's `BaseToolkit` and returns native `StructuredTool` instances. Pass the list to a configured agent or call `invoke`/`ainvoke` directly. The four tool names are `sarj_list_calls`, `sarj_get_call`, `sarj_get_call_transcript`, and `sarj_get_call_analysis`. Each has a strict public JSON input schema and validates inputs before any HTTP request.

List Calls supports filters and an explicit next-page cursor. Other reads take a call UUID. Responses retain the service's JSON object and null values. Tools never discover or expose write operations. Their descriptions and schemas do not contain credentials, and the toolkit's private client is omitted from model dumps.

Await all tool work before closing the toolkit/client. Every HTTP invocation owns its response and connection lifecycle; the default deadline is 30 seconds. Use async invocation from an async agent. Core errors have a safe code and optional HTTP status; raw bodies, input values and upstream exceptions are not included.

The application controls approvals, authorization, model use and tracing. Outputs can contain confidential information and can enter your model provider or tracing system. The package does not enable telemetry or read a default credential from the environment. See the main README for response-size limits and privacy requirements.

Offline examples from the source checkout:

```sh
HAYSTACK_TELEMETRY_ENABLED=false LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false uv run python examples/synthetic.py
```

This exercises real LangChain tools and Haystack tools against synthetic transport data. It performs no live Sarj/model call. Support: engineering@sarj.ai. License: MIT.
