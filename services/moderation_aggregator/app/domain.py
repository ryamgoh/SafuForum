"""Domain models for the Moderation Aggregator Service."""
from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator, Field

class Status(str, Enum):
    """Enumeration of possible moderation statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"

    @classmethod
    def _missing_(cls, _):
        return cls.FAILED

class ResultEvent(BaseModel):
    """Event representing the result of a moderation job."""
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        use_enum_values=True,
        extra="ignore",
    )
    service_name: str | None = Field(default=None, alias="serviceName")
    # Use Field with a default to make the validator's job easier
    status: Status = Field(default=Status.FAILED)
    reason: str | None = None

    @field_validator("service_name", mode="before")
    @classmethod
    def _coerce_service_name(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8")
            except Exception:
                value = value.decode("utf-8", errors="replace")
        normalized = str(value).strip()
        return normalized or None

    @field_validator("status", mode="before")
    @classmethod
    def _coerce_status(cls, value: Any) -> Any:
        # If it's None or an empty string, treat as FAILED
        if value is None or value == "":
            return Status.FAILED
        return value # Status(value) will now trigger _missing_ if invalid

class JobCompletedEvent(BaseModel):
    """Event representing the completion of a moderation job."""
    model_config = ConfigDict(frozen=True, populate_by_name=True, use_enum_values=True)
    # Using 'Status' (the Enum) is safer than 'str' for consistency
    status: Status
    reason: str
