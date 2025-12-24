from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class ModerationJob(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    payload: str = ""

    @field_validator("payload", mode="before")
    @classmethod
    def _coerce_payload(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value)


class ModerationDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    reason: str


class ModerationJobCompletedEvent(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    status: str
    reason: str
