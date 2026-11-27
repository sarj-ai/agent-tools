# Sarj AI agent tools

<img src="https://raw.githubusercontent.com/sarj-ai/mcp-integrations/main/assets/logo.png" alt="Sarj AI — سرج" width="180" />

Four read tools for [Sarj AI](https://sarj.ai)'s Arabic-first enterprise voice platform, exposed through native LangChain and Haystack interfaces. Both adapters share a small client for four existing REST GET endpoints. No backend deployment is needed.

LangChain and Haystack catalog availability depends on their respective maintainer reviews. This package does not claim either catalog's approval.

| Tool name | Existing GET route | Reads |
| --- | --- | --- |
| `sarj_list_calls` | `/calls` | One page of recent calls, newest first |
| `sarj_get_call` | `/calls/{call_id}` | Details, status, duration and latest outcome |
| `sarj_get_call_transcript` | `/calls/{call_id}/transcript` | Available turns, UTC times and call offsets |
| `sarj_get_call_analysis` | `/calls/{call_id}/analysis` | Collected data, outcome, caller experience and quality flags |

The fixed API base is `https://platform-api.sarj.ai/api/v1`. The package does not discover other operations, expose a generic HTTP tool, generate voice, place calls, or modify records.

## Before using the tools

Use Python 3.11+ and an existing Sarj organization account. Create an API key with **`calls:read` only** on the [API keys page](https://platform.sarj.ai/api-keys). Your role must permit API credential creation and access to the intended calls. Organization membership, pilot entitlement and enabled features can restrict individual reads; a valid key does not bypass those gates. Contact your administrator or [engineering@sarj.ai](mailto:engineering@sarj.ai) if denied.

Pass the raw key explicitly to each client or adapter, without the `Bearer ` prefix. The package never reads a credential from the environment, starts OAuth, refreshes tokens or expands scopes. It cannot reduce the permissions of a broader credential.

## Install the framework you use

```sh
pip install 'sarj-agent-tools[langchain]'
# Or:
pip install 'sarj-agent-tools[haystack]'
# Both:
pip install 'sarj-agent-tools[all]'
```

The base package needs only HTTPX and Pydantic. The LangChain extra uses `langchain-core`, not a model-provider package. The Haystack extra uses `haystack-ai` 3.5+. Importing `sarj_agent_tools` does not import either framework. This release is tested against LangChain Core 1.8.5 and Haystack 3.5.0.

## LangChain

`SarjToolkit` implements `BaseToolkit`; `get_tools()` returns four native `StructuredTool` instances. Supply the key from your application's secret store:

```python
from sarj_agent_tools.langchain import SarjToolkit

def read_recent_calls(api_key: str) -> dict:
    with SarjToolkit(api_key=api_key) as toolkit:
        tools = {tool.name: tool for tool in toolkit.get_tools()}
        return tools["sarj_list_calls"].invoke({"limit": 3, "status": "completed"})
```

Pass `toolkit.get_tools()` to your configured LangChain agent if desired. For async execution, await `tool.ainvoke(...)` before closing. See the [LangChain guide](docs/langchain.md).

## Haystack

`SarjToolset` implements `Toolset` and contains four native `Tool` subclasses. Their safe invocation methods avoid the upstream default error wrapper that echoes tool arguments.

```python
from sarj_agent_tools.haystack import SarjToolset

def read_transcript(api_key: str, call_id: str) -> dict:
    with SarjToolset(api_key=api_key) as toolset:
        tools = {tool.name: tool for tool in toolset}
        return tools["sarj_get_call_transcript"].invoke(call_id=call_id)
```

Use `await tool.invoke_async(...)` in async code, or pass the toolset to your Haystack agent. The [Haystack guide](docs/haystack.md) includes the supported API and a runnable synthetic Pipeline example.

## Inputs, results and errors

List Calls accepts optional `scenario_id`, `status`, `created_from` (inclusive), `created_to` (exclusive), `limit` (integer 1–100; default 20), `cursor` (at most 128 characters), and `organization_id`. Nullable filters may be omitted or set to `None`. Date-times must include a timezone. Only Sarj super admins can target an organization other than their key's organization.

The other tools require a `call_id` UUID from List Calls. Public OpenAPI describes Get Call's ID as a UUID but types that one parameter as an unconstrained string; this adapter validates UUID syntax for every call path. Unknown fields, coercions such as `limit="2"`, booleans as limits, invalid identifiers, and unbounded cursors are rejected before transport.

The service's JSON response object is preserved, including nested data and null values. No call-output model or invented outcome is imposed. A list request reads one page; supply the returned cursor explicitly for the next. Transcript availability depends on processing and organization features, and unfinished analysis may remain null.

Core/LangChain failures are `SarjToolError` instances with a safe `code` and optional HTTP `status`. Haystack uses its standard `ToolInvocationError` with the same safe code in the message. Codes include `INVALID_INPUT`, `AUTHENTICATION`, `AUTHORIZATION`, `NOT_FOUND`, `RATE_LIMITED`, `HTTP_ERROR`, `PROTOCOL`, `CONNECTION`, `TIMEOUT`, `RESPONSE_TOO_LARGE`, `CLOSED`, and `ASYNC_REQUIRED`. Raw upstream bodies, request objects, keys and exception causes are not attached. A denied or missing read is not silently converted to empty data.

## Deadlines and lifecycle

Each request owns and closes its HTTP client and response, including on errors, deadline expiry and async cancellation. The default overall HTTP deadline is 30 seconds and the JSON response limit is 16 MiB. There are no application retries, automatic pagination or redirects. HTTP proxy/auth environment defaults are disabled and requests use `Cache-Control: no-store`.

For custom limits or a trusted synthetic transport, construct `SarjReadClient(api_key=..., timeout=..., max_response_bytes=..., transport_factory=...)` and pass `client=client` to either adapter. The timeout must be greater than zero and at most 300 seconds; response limits are 1 byte–64 MiB. Each transport returned by the factory is owned and closed by that invocation. It receives authentication headers, so never log those headers.

`close()` is idempotent and prevents new reads. Await active work before closing; in-flight work keeps its own deadline/cancellation cleanup. Sync tools must run outside an active event loop; use the native async interfaces in async applications. Clients are not picklable, LangChain toolkit dumps omit the private client, and Haystack serialization raises `SerializationError`. Recreate bound tools with an explicit credential in each process rather than serializing keys.

## Privacy

Call data and transcripts may contain personal or confidential information. Enforce application-user and tenant access before exposing tools. Tool outputs may be stored in framework traces, flow state, downstream systems or sent to your chosen model provider. Review those systems' policies and minimize returned data.

This package emits no logs or telemetry and persists no credential or response store. HTTP/framework logging, tracing and telemetry have their own application-controlled settings. The offline verification commands explicitly disable framework telemetry/tracing; the package does not change global application settings. Never include keys or unredacted call data in source, logs or public reports. [Privacy](https://sarj.ai/privacy), [terms](https://sarj.ai/terms), [MCP/service docs](https://platform-docs.sarj.ai/mcp-server).

## Develop and verify

```sh
uv sync --python 3.11 --all-extras --group dev
make check
```

The examples and tests use synthetic HTTP transports and current native framework APIs, with no Sarj or model-provider request. `make check` runs lint, tests, build/metadata checks, the two examples and isolated wheel-consumer checks. The consumers install the base package and each extra separately from the built wheel; installation may download public dependencies, and tool invocation blocks external sockets. Release and intake drafts are in [docs/intake](docs/intake); source publication, live organization-gate verification, PyPI publication and catalog approval remain release-owner tasks.

The public `sarj-platform-sdk` 0.4.4 wheel was checked first. It supports Get Call but lacks List Calls, Get Call Transcript and Get Call Analysis. This small shared client covers those four current reads without fabricating SDK methods or adding backend routes.

## License and support

MIT. Sarj's name and logos remain brand assets. Support: [engineering@sarj.ai](mailto:engineering@sarj.ai).
