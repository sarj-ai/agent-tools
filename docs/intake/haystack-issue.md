# Haystack integration proposal

Submitted proposal: https://github.com/deepset-ai/haystack-integrations/issues/798. Maintain that issue; do not create a duplicate.

Current intake begins with the [new integration issue](https://github.com/deepset-ai/haystack-integrations/issues/new?template=new-integration.yml). Wait for a maintainer's `approved` label before opening the showcase PR. The repository README is more specific than the general documentation page's direct-PR wording.

| Form field | Candidate value |
| --- | --- |
| Stage | Ready: integration exists and works, proposing to list it |
| Integration or project name | Sarj AI |
| Integration type | Tool Integration |
| Published package or repo | [Public source](https://github.com/sarj-ai/agent-tools); [PyPI](https://pypi.org/project/sarj-agent-tools/) after release verification |
| Need or proof of use | [Real Haystack Pipeline](https://github.com/sarj-ai/agent-tools/blob/main/examples/haystack_pipeline.py) consuming a native Sarj tool with synthetic transport data; 72 tests and installed consumers pass. All four tools also passed bounded sync/async live reads in an isolated synthetic workspace. No production customer-use claim is made. |
| Short description | Four read tools let a Haystack agent or pipeline inspect an authorized Sarj organization's call history, details, transcripts and analysis. They use per-instance read-scoped credentials and expose no voice generation or call management. |

The package exposes a supported `Toolset`/`Tool` interface for Haystack 3.5+. It is independently maintained by Sarj AI. The synthetic pipeline demonstrates compatibility without a provider key or customer payload; it is not proof of live organization entitlement or production adoption.

After approval, the proposed showcase files are `integrations/sarj.md` (candidate in this folder) and `logos/sarj.png` (copy the existing official `assets/logo.png`). Confirm the site's accepted Haystack-version label rather than incorrectly claiming Haystack 2 compatibility.

Official sources: [repository intake policy](https://github.com/deepset-ai/haystack-integrations#how-to-contribute), [issue schema](https://github.com/deepset-ai/haystack-integrations/blob/main/.github/ISSUE_TEMPLATE/new-integration.yml), [integration draft](https://github.com/deepset-ai/haystack-integrations/blob/main/draft-integration.md).
