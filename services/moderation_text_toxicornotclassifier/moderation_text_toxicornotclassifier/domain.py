from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModerationJob:
    moderation_job_id: int | None
    post_id: int | None
    post_version: int | None
    content_type: str | None
    payload: str


@dataclass(frozen=True)
class ModerationDecision:
    status: str
    reason: str


@dataclass(frozen=True)
class ModerationJobCompletedEvent:
    moderation_job_id: int | None
    post_id: int | None
    post_version: int | None
    status: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "moderationJobId": self.moderation_job_id,
            "postId": self.post_id,
            "postVersion": self.post_version,
            "status": self.status,
            "reason": self.reason,
        }

