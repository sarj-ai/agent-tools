---
layout: integration
name: Sarj AI
description: Read authorized Sarj call history, details, available transcripts and analysis with Haystack tools.
authors:
  - name: Sarj AI
    socials:
      github: sarj-ai
pypi: https://pypi.org/project/sarj-agent-tools/
type: Tool Integration
logo: /logos/sarj.png
version: Haystack 3.5
toc: true
---

<!-- DRAFT: add the actual public repo/report_issue URLs and approved intake issue before submission. The package is not published yet. Confirm the site's version-label convention. -->

## Overview

`SarjToolset` supplies four native Haystack tools for an authorized Sarj organization's call history, call details, transcripts and analysis. The package uses four existing REST GET routes. No voice generation, call placement or record modification is exposed.

Use an existing Sarj organization account and a `calls:read` API key created by an eligible account role. Individual reads remain subject to organization/pilot entitlement and feature availability. Support: engineering@sarj.ai.

## Installation

```sh
pip install 'sarj-agent-tools[haystack]'
```

Requires Python 3.11+ and Haystack 3.5+. This is a draft command until PyPI publication.

## Usage

```python
from sarj_agent_tools.haystack import SarjToolset

def read_recent_calls(api_key: str) -> dict:
    with SarjToolset(api_key=api_key) as toolset:
        tools = {tool.name: tool for tool in toolset}
        return tools["sarj_list_calls"].invoke(limit=3)
```

The tools are `sarj_list_calls`, `sarj_get_call`, `sarj_get_call_transcript`, and `sarj_get_call_analysis`. Native async invocation is available through `invoke_async`; a configured Agent can consume the toolset. Map a call UUID from List Calls into the other reads. Returned JSON envelopes and null/pending values are preserved.

The public source will include a runnable synthetic Haystack Pipeline example and tests. Add its actual link before submission. Those examples require no model-provider key and do not claim production usage.

Inputs are strict and bounded. HTTP work has a deadline and each invocation owns connection cleanup. Errors omit raw inputs, bodies and credentials. Bound credentials are not serialized; recreate the toolset with an explicit key in each process. The application controls authorization, tracing, model use and output storage.

## License

MIT. Sarj's name and logos remain brand assets. [Privacy](https://sarj.ai/privacy), [terms](https://sarj.ai/terms), and [support](mailto:engineering@sarj.ai).
