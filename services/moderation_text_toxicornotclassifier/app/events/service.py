from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.domain import ModerationDecision, ModerationJob, ModerationJobCompletedEvent
from app.inference.service import TextInferenceService


@dataclass(frozen=True)
class ProcessedEvent:
    completion: ModerationJobCompletedEvent
    correlation_id: str | None


def _decode_json(body: bytes) -> dict[str, Any]:
    try:
        decoded = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("payload is not valid UTF-8") from exc
    try:
        value = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise ValueError("payload is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def _resolve_correlation_id(incoming: str | None, job: ModerationJob) -> str | None:
    if incoming:
        return str(incoming)
    if job.moderation_job_id is None:
        return None
    return str(job.moderation_job_id)


class ModerationEventService:
    def __init__(self, inference_service: TextInferenceService) -> None:
        self._inference_service = inference_service

    def handle_message(self, *, body: bytes, correlation_id: str | None) -> ProcessedEvent:
        try:
            raw_event = _decode_json(body)
        except Exception as exc:
            completion = ModerationJobCompletedEvent(
                moderation_job_id=None,
                post_id=None,
                post_version=None,
                status="failed",
                reason=str(exc),
            )
            return ProcessedEvent(completion=completion, correlation_id=correlation_id)

        try:
            job = ModerationJob.model_validate(raw_event)
        except ValidationError as exc:
            completion = ModerationJobCompletedEvent(
                moderation_job_id=None,
                post_id=None,
                post_version=None,
                status="failed",
                reason=str(exc),
            )
            return ProcessedEvent(completion=completion, correlation_id=correlation_id)

        resolved_correlation_id = _resolve_correlation_id(correlation_id, job)

        content_type = (job.content_type or "").lower()
        if content_type and content_type != "text":
            decision = ModerationDecision(status="failed", reason=f"unexpected_content_type:{content_type}")
        else:
            try:
                decision = self._inference_service.classify_text(job.payload)
            except Exception as exc:
                decision = ModerationDecision(status="failed", reason=str(exc))

        completion = ModerationJobCompletedEvent(
            moderation_job_id=job.moderation_job_id,
            post_id=job.post_id,
            post_version=job.post_version,
            status=decision.status,
            reason=decision.reason,
        )
        return ProcessedEvent(completion=completion, correlation_id=resolved_correlation_id)
