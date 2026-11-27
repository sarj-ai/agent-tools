"""Strict public inputs for the four call reads."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

UUID_TEXT = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
UuidText = Annotated[str, Field(pattern=UUID_TEXT, json_schema_extra={"format": "uuid"})]
CallStatus = Literal[
    "queued",
    "in_progress",
    "transferring",
    "transferred",
    "completed",
    "timeout",
    "user_rejected",
    "max_duration_reached",
    "failed",
    "ringing",
    "voicemail",
    "dialing",
    "cancelled",
    "expired",
    "scheduled",
]


class ListCallsInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    scenario_id: UuidText | None = None
    status: CallStatus | None = None
    created_from: Annotated[
        str | None, Field(max_length=64, json_schema_extra={"format": "date-time"})
    ] = None
    created_to: Annotated[
        str | None, Field(max_length=64, json_schema_extra={"format": "date-time"})
    ] = None
    limit: Annotated[int, Field(ge=1, le=100)] = 20
    cursor: Annotated[str | None, Field(max_length=128)] = None
    organization_id: UuidText | None = Field(
        default=None,
        description="Only Sarj super admins may target another org; omit for the key's org.",
    )

    @field_validator("created_from", "created_to")
    @classmethod
    def timezone_date_time(cls, value: str | None) -> str | None:
        if value is not None:
            if not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})", value
            ):
                raise ValueError("Use a timezone-aware ISO date-time.")
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("A timezone is required.")
        return value


class CallInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)
    call_id: UuidText = Field(description="Call UUID returned in the id field of List Calls.")


@dataclass(frozen=True)
class ReadSpec:
    operation: str
    tool_name: str
    description: str
    input_model: type[BaseModel]
    suffix: str | None


READ_SPECS = (
    ReadSpec(
        "list_calls",
        "sarj_list_calls",
        "Read one page of the organization's recent calls, newest first. Filter by status, "
        "scenario, creation time or cursor. At most 100 per page; no call is modified.",
        ListCallsInput,
        None,
    ),
    ReadSpec(
        "get_call",
        "sarj_get_call",
        "Read one call's details, status, duration and latest outcome using its call UUID.",
        CallInput,
        "",
    ),
    ReadSpec(
        "get_call_transcript",
        "sarj_get_call_transcript",
        "Read available conversation turns, UTC times and call offsets for a call UUID. "
        "Access and availability depend on organization features and processing.",
        CallInput,
        "/transcript",
    ),
    ReadSpec(
        "get_call_analysis",
        "sarj_get_call_analysis",
        "Read collected data, outcome, caller experience and quality flags for a call UUID. "
        "Pending analysis may contain null fields; organization access is required.",
        CallInput,
        "/analysis",
    ),
)
