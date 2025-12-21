from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModerationJob(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="ignore")

    moderation_job_id: int | None = Field(default=None, alias="moderationJobId")
    post_id: int | None = Field(default=None, alias="postId")
    post_version: int | None = Field(default=None, alias="postVersion")
    content_type: str | None = Field(default=None, alias="contentType")
    payload: str = ""

    @field_validator("moderation_job_id", "post_id", "post_version", mode="before")
    @classmethod
    def _coerce_optional_int(cls, value: object) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return int(value)
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    @field_validator("content_type", mode="before")
    @classmethod
    def _coerce_content_type(cls, value: object) -> str | None:
        if value is None or value == "":
            return None
        return str(value)

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

    moderation_job_id: int | None = Field(default=None, alias="moderationJobId")
    post_id: int | None = Field(default=None, alias="postId")
    post_version: int | None = Field(default=None, alias="postVersion")
    status: str
    reason: str
