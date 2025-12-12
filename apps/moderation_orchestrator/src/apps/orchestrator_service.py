"""Orchestrator flow: fan-out, aggregate via DB, persist, publish."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Iterable, List

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    ImageData,
    Status,
    JobTask,
    ModerationJob,
    TextData,
    Verdict,
)
from helpers import messaging
from repositories.decisions import upsert_decision

# TODO: drive from config/DB
TEXT_SERVICE_TARGETS: tuple[str, ...] = ("text-moderator-1",)
IMAGE_SERVICE_TARGETS: tuple[str, ...] = ("image-moderator-1",)


async def _seed_job_and_tasks(
    session: AsyncSession, correlating_id: str, content: Dict[str, Any]
) -> List[str]:
    """Ensure a ModerationJob, content rows, and JobTasks exist for the given content."""
    job = await session.get(ModerationJob, correlating_id)
    if not job:
        session.add(
            ModerationJob(
                correlating_id=correlating_id,
                content_id=content.get("content_id"),
                submitter_id=content.get("submitter_id"),
                status=Status.PENDING,
            )
        )

    # Seed modality-specific content tables
    if content.get("text") is not None:
        existing_text = await session.get(TextData, correlating_id)
        if not existing_text:
            session.add(TextData(correlating_id=correlating_id, text_excerpt=content.get("text")))
    if content.get("image_uri"):
        existing_image = await session.get(ImageData, correlating_id)
        if not existing_image:
            session.add(ImageData(correlating_id=correlating_id, image_uri=content["image_uri"]))

    # Build target list based on persisted content rows
    targets: list[str] = []
    if await session.get(TextData, correlating_id):
        targets.extend(list(TEXT_SERVICE_TARGETS))
    if await session.get(ImageData, correlating_id):
        targets.extend(list(IMAGE_SERVICE_TARGETS))

    # Insert tasks if they don't exist yet
    for event_name in targets:
        exists_stmt = select(JobTask.id).where(
            and_(JobTask.correlating_id == correlating_id, JobTask.event_name == event_name)
        )
        existing = await session.execute(exists_stmt)
        if existing.scalar_one_or_none() is None:
            session.add(
                JobTask(
                    correlating_id=correlating_id,
                    event_name=event_name,
                    status=Status.PENDING,
                )
            )

    return targets


async def _publish_fanout(correlating_id: str, targets: Iterable[str], content: Dict[str, Any]) -> None:
    """Publish a task request per target service."""
    for event_name in targets:
        await messaging.publish_task_request(
            correlation_id=correlating_id,
            event_name=event_name,
            payload={"correlating_id": correlating_id, "event_name": event_name, "content": content},
        )


def _aggregate_verdict(tasks: List[JobTask], timed_out: bool) -> Verdict:
    """Fold task payloads into a single verdict."""
    verdicts = set()
    for task in tasks:
        payload = task.payload or {}
        v = payload.get("verdict")
        if v:
            verdicts.add(Verdict(v))
    if Verdict.block in verdicts:
        return Verdict.block
    if Verdict.error in verdicts or Verdict.review in verdicts:
        return Verdict.review
    if timed_out:
        return Verdict.review
    return Verdict.allow


def _average_score(tasks: List[JobTask]) -> float | None:
    scores = []
    for task in tasks:
        payload = task.payload or {}
        score = payload.get("score")
        if score is not None:
            scores.append(float(score))
    if not scores:
        return None
    return sum(scores) / len(scores)


async def run_orchestrator(event: Dict[str, Any], session: AsyncSession) -> Dict[str, Any]:
    """
    Normalize, seed job/tasks, publish fan-out, await DB-driven completion, persist, and publish.

    Note: completion waiting is expected to be driven by inbound events updating job_tasks.
    """
    correlating_id = event.get("correlating_id") or event.get("job_id") or event.get("request_id") or str(uuid.uuid4())
    content = event.get("content", {})

    async with session.begin():
        targets = await _seed_job_and_tasks(session, correlating_id, content)
        await _publish_fanout(correlating_id, targets, content)

    return {"correlating_id": correlating_id, "published_to": targets}


async def handle_task_completed(event: Dict[str, Any], session: AsyncSession) -> Dict[str, Any]:
    """
    Handle a service completion event: update job_task, check if all tasks are terminal,
    finalize decision if ready, and publish completion.
    """
    correlating_id = event["correlation_id"]
    event_name = event["service_id"]
    payload = event.get("payload") or {}
    verdict_str = payload.get("verdict")
    verdict = Verdict(verdict_str) if verdict_str else None

    async with session.begin():
        # Update the matching task
        update_stmt = (
            update(JobTask)
            .where(and_(JobTask.correlating_id == correlating_id, JobTask.event_name == event_name))
            .values(
                status=Status.COMPLETED,
                payload=payload,
            )
            .returning(JobTask)
        )
        task_result = await session.execute(update_stmt)
        updated_task = task_result.scalar_one_or_none()

        # If no task matched, ignore
        if not updated_task:
            return {"correlating_id": correlating_id, "status": "ignored"}

        # Check remaining tasks
        tasks_stmt = select(JobTask).where(JobTask.correlating_id == correlating_id)
        tasks_result = await session.execute(tasks_stmt)
        tasks = list(tasks_result.scalars())

        all_terminal = all(t.status in {Status.COMPLETED, Status.FAILED, Status.TIMED_OUT} for t in tasks)
        timed_out = any(t.status == Status.TIMED_OUT for t in tasks)

        if not all_terminal:
            return {"correlating_id": correlating_id, "status": "pending"}

        final_verdict = _aggregate_verdict(tasks, timed_out)
        decision_payload = {
            "correlating_id": correlating_id,
            "final_verdict": final_verdict,
            "timed_out": timed_out,
        }

        await upsert_decision(session, decision_payload)

    await messaging.publish_completed(
        original_event=event,
        decision={
            "correlating_id": correlating_id,
            "verdict": final_verdict.value,
            "timed_out": timed_out,
            "responses": [t.payload for t in tasks],
        },
    )

    return {"correlating_id": correlating_id, "status": "completed", "verdict": final_verdict.value}
