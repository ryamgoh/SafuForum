from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from moderation_text_toxicornotclassifier.domain import ModerationDecision, ModerationJobCompletedEvent
from moderation_text_toxicornotclassifier.inference.service import TextInferenceService


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


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _resolve_correlation_id(incoming: str | None, event: dict[str, Any]) -> str | None:
    if incoming:
        return str(incoming)
    job_id = event.get("moderationJobId")
    if job_id is None:
        return None
    return str(job_id)


class ModerationEventService:
    def __init__(self, inference_service: TextInferenceService) -> None:
        self._inference_service = inference_service

    def handle_message(self, *, body: bytes, correlation_id: str | None) -> ProcessedEvent:
        try:
            event = _decode_json(body)
        except Exception as exc:
            completion = ModerationJobCompletedEvent(
                moderation_job_id=None,
                post_id=None,
                post_version=None,
                status="failed",
                reason=str(exc),
            )
            return ProcessedEvent(completion=completion, correlation_id=correlation_id)

        resolved_correlation_id = _resolve_correlation_id(correlation_id, event)

        content_type = str(event.get("contentType") or "").lower()
        if content_type and content_type != "text":
            decision = ModerationDecision(status="failed", reason=f"unexpected_content_type:{content_type}")
        else:
            try:
                decision = self._inference_service.classify_text(str(event.get("payload") or ""))
            except Exception as exc:
                decision = ModerationDecision(status="failed", reason=str(exc))

        completion = ModerationJobCompletedEvent(
            moderation_job_id=_coerce_int(event.get("moderationJobId")),
            post_id=_coerce_int(event.get("postId")),
            post_version=_coerce_int(event.get("postVersion")),
            status=decision.status,
            reason=decision.reason,
        )
        return ProcessedEvent(completion=completion, correlation_id=resolved_correlation_id)

