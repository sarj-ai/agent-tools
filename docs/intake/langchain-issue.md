# LangChain Integration listing issue — draft

Submit only after the package and source/docs are public. Current intake: [Integration listing form](https://github.com/langchain-ai/docs/issues/new?template=06-integration-submission.yml). A maintainer applies `integration-run`; do not self-apply it or open a manual listing/hosted-guide PR. Below 50,000 monthly downloads, unless featured by maintainers, the default route is an external listing.

| Form field | Candidate value |
| --- | --- |
| Display or class name | SarjToolkit |
| Language | Python |
| Component type | tools |
| PyPI package name | sarj-agent-tools |
| npm package name | Leave blank |
| Docs URL | https://github.com/sarj-ai/agent-tools/blob/main/docs/langchain.md |
| Source repository | https://github.com/sarj-ai/agent-tools |
| Short provider description | Four read tools for Sarj AI call history, details, transcripts and analysis, using scoped organization API keys. |
| Capability flags | Leave blank; chat/vector-store flags do not apply |
| Published-package confirmation | Unchecked until the PyPI artifact is public |

The toolkit implements `BaseToolkit` and creates four `StructuredTool` objects with native sync and async invocation. The [source and tests](https://github.com/sarj-ai/agent-tools), [LangChain guide](https://github.com/sarj-ai/agent-tools/blob/main/docs/langchain.md), and [PyPI page](https://pypi.org/project/sarj-agent-tools/) are the submission links; verify the PyPI artifact before submitting. Public CI covers 72 tests, synthetic examples and installed-wheel consumers. All four native LangChain tools also passed bounded sync and async reads against an isolated synthetic workspace; no keys or response payloads are included. Do not claim hosted-guide eligibility, maintainer endorsement or production usage.

Official instructions: [publish/listing guide](https://docs.langchain.com/oss/python/contributing/publish-langchain), [current issue schema](https://github.com/langchain-ai/docs/blob/main/.github/ISSUE_TEMPLATE/06-integration-submission.yml).
