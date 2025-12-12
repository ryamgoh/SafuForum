"""Decision persistence and retrieval using SQLAlchemy."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import JobStatus, ModerationDecision, ModerationJob


def _decision_to_dict(decision: ModerationDecision) -> Dict[str, Any]:
    """Serialize a ModerationDecision into a plain dict."""
    return {
        "job_id": str(decision.job_id),
        "final_verdict": decision.final_verdict.value,
        "final_score": float(decision.final_score) if decision.final_score is not None else None,
        "rationale": decision.rationale,
        "timed_out": decision.timed_out,
        "task_count": decision.task_count,
        "decided_at": decision.decided_at,
    }


async def upsert_decision(session: AsyncSession, payload: Dict[str, Any]) -> ModerationDecision:
    """
    Store the composite decision. Creates or updates by job_id.

    `payload` should include: job_id, final_verdict, final_score (optional),
    rationale (optional), timed_out (bool), task_count (optional).
    """
    job_id = payload["job_id"]

    decision = await session.get(ModerationDecision, job_id)
    if decision:
        decision.final_verdict = payload["final_verdict"]
        decision.final_score = payload.get("final_score")
        decision.rationale = payload.get("rationale")
        decision.timed_out = payload.get("timed_out", False)
        decision.task_count = payload.get("task_count")
    else:
        decision = ModerationDecision(**payload)
        session.add(decision)

    # Update job lifecycle if present
    job = await session.get(ModerationJob, job_id)
    if job:
        job.status = JobStatus.completed

    # Caller is responsible for committing
    return decision


async def fetch_decision(session: AsyncSession, job_id: str) -> Optional[Dict[str, Any]]:
    """Return a prior decision for a given job to support idempotency."""
    stmt = select(ModerationDecision).where(ModerationDecision.job_id == job_id)
    result = await session.execute(stmt)
    decision = result.scalar_one_or_none()
    if decision is None:
        return None
    return _decision_to_dict(decision)
