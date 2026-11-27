# Release owner checklist

Source: https://github.com/sarj-ai/agent-tools. The release workflow verifies the package before PyPI Trusted Publishing. LangChain and Haystack catalog publication remains subject to their maintainer reviews. Maintainer: Sarj AI, engineering@sarj.ai. License: MIT; existing Sarj brand logo is in `assets/logo.png`.

## Concrete release artifact

- Distribution: `sarj-agent-tools`, candidate version `0.1.0`; import `sarj_agent_tools`.
- Python: `>=3.11,<4`; base dependencies: HTTPX and Pydantic.
- Optional extras: `langchain`, `haystack`, `all`; the base import loads neither framework. Tested native interfaces: LangChain Core 1.8.5 and Haystack 3.5.0.
- Four fixed existing GET routes under `https://platform-api.sarj.ai/api/v1`: `/calls`, `/calls/{call_id}`, `/calls/{call_id}/transcript`, `/calls/{call_id}/analysis`.
- Supply one raw `calls:read` API key per instance. No credential environment fallback, OAuth, writes, generic HTTP tool or backend change.
- Account role, organization membership, pilot entitlement and enabled features remain enforced by Sarj. Live checks on 27 November 2026 exercised all four reads synchronously and asynchronously through both native adapters, using only the isolated synthetic reviewer organization. No call contents or credentials were saved. Eligibility for any other organization is not implied.

The current public `sarj-platform-sdk==0.4.4` wheel implements Get Call but not the other three reads. This package therefore uses one fixed-route HTTPX client for both adapters. Recheck the official SDK before a future transport migration; preserve strict inputs, deadlines, sanitized errors and ownership of cleanup.

## Before publishing

1. Choose a Sarj-owned public source repository and publish the reviewed source through the authorized release workflow. Add its real source and issue-tracker URLs to `pyproject.toml`; do not advertise a nonexistent URL. The present homepage, general documentation and support URLs already exist.
2. Run a bounded live read check with a synthetic organization/call and a temporary `calls:read` credential, respecting actual organization/pilot gates. Record only operation/status metadata and cleanup evidence. Do not publish credentials or call contents. Test an insufficient-scope/organization denial where available. A denied endpoint must remain an explicit failure.
3. Publish or link the LangChain and Haystack guides from the actual source/docs location. Replace all intake placeholders. Remove or update the README's unpublished-candidate paragraph when the release becomes public; keep it truthful throughout.
4. Verify the package name is still available and the release identity can own it. Search checks do not reserve a PyPI name. Rebuild after changing metadata or docs.

## Local gates and installation dry-run

```sh
uv sync --python 3.11 --all-extras --group dev
make check
```

`make check` includes Ruff, synthetic network-blocked tests, wheel/sdist creation, Twine metadata checks, native-framework examples, and fresh isolated consumers for base/LangChain/Haystack. Those consumers run installer dry-runs, install the actual wheel, assert optional dependency isolation, invoke the four native tools synchronously and asynchronously, and check request cleanup. Installation may download public registry dependencies; tool execution blocks external sockets. Twine 7+ is required for the builder's metadata 2.5; no credentials are used by `twine check`.

After the release owner authorizes publication and configures its chosen trusted publishing workflow or secret store, publish the exact reviewed distributions to PyPI. The release workflow uses the PyPI Trusted Publisher bound to this repository, publish.yml, and the pypi environment. Do not place registry tokens in this repository. Candidate public page: `https://pypi.org/project/sarj-agent-tools/` only after publication. The base package name is the catalog field; extras belong only in installation commands.

## Catalog sequence

LangChain: complete [the integration listing issue](https://github.com/langchain-ai/docs/issues/new?template=06-integration-submission.yml) using `langchain-issue.md` after PyPI/source/docs are public. Under 50,000 monthly downloads, unless maintainers feature the integration, use the external listing path. A maintainer applies `integration-run`; its automation manages the listing. Do not open a manual listing/hosted-guide PR.

Haystack: complete [the new-integration proposal](https://github.com/deepset-ai/haystack-integrations/issues/new?template=new-integration.yml) using `haystack-issue.md`. Follow the current repository README: wait for maintainer `approved` before a showcase PR. After approval, adapt `sarj.md`, add the actual repository/report-issue links and copy `assets/logo.png` to `logos/sarj.png`. Confirm the showcase's version-label convention; this candidate has been checked on Haystack 3.5, not 2.x. Link the real synthetic Pipeline as compatibility evidence and separately state live verification; do not invent customer adoption.

Both catalogs remain subject to maintainer review. A PyPI package alone is not a catalog listing.
