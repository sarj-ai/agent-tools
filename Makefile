.PHONY: check lint test build example consumer

check: lint test build example consumer

lint:
	uv run ruff check src tests examples scripts
	uv run ruff format --check src tests examples scripts

test:
	HAYSTACK_TELEMETRY_ENABLED=false LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false uv run pytest

build:
	uv build
	uv run twine check dist/*

example:
	HAYSTACK_TELEMETRY_ENABLED=false LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false uv run python examples/synthetic.py
	HAYSTACK_TELEMETRY_ENABLED=false LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false uv run python examples/haystack_pipeline.py

consumer: build
	uv run python scripts/check_wheel.py dist/sarj_agent_tools-0.1.0-py3-none-any.whl
