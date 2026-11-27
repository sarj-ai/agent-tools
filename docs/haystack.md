# SarjToolset for Haystack

Install `pip install 'sarj-agent-tools[haystack]'`. This integration targets Haystack 3.5+, not the older Haystack 2 APIs. Use Python 3.11+ and an existing Sarj organization key with `calls:read`; role, organization and pilot restrictions still apply.

```python
from sarj_agent_tools.haystack import SarjToolset

async def inspect_call(api_key: str, call_id: str) -> dict:
    with SarjToolset(api_key=api_key) as toolset:
        tools = {tool.name: tool for tool in toolset}
        return await tools["sarj_get_call_analysis"].invoke_async(call_id=call_id)
```

`SarjToolset` is a native `Toolset` containing four `Tool` subclasses. Each supports `invoke(**arguments)` and native `invoke_async(**arguments)`. A configured Haystack `Agent` can accept the toolset. This package does not select a model or require model-provider credentials itself.

The four provided tools read call history, call details, available transcripts and analysis. Inputs are bounded and strict; responses preserve the API JSON envelope. Read denials are raised through Haystack's standard `ToolInvocationError` with safe messages that omit input values, response bodies and credentials.

Bound tools deliberately reject `to_dict`/`from_dict` credential serialization. Construct the toolset with your application's explicit credential when the process starts. Client pickling is also rejected. Await active calls before closing; every request owns its HTTP cleanup and deadline.

The source contains a complete real Haystack Pipeline example. A small example component invokes the native `sarj_get_call` tool, and a synthetic HTTP transport supplies its response:

```sh
HAYSTACK_TELEMETRY_ENABLED=false LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false uv run python examples/haystack_pipeline.py
```

The example needs no Sarj account or LLM. It is synthetic compatibility evidence, not a claim of production deployment or live organization access. `examples/synthetic.py` additionally exercises all four tools through both frameworks' async interfaces.

The application controls connection access, downstream data storage, tracing and model-provider policies. Call contents can be confidential; never log keys or unredacted results. See the README for deadline/size limits, account requirements and service privacy/terms. Support: engineering@sarj.ai. License: MIT.
