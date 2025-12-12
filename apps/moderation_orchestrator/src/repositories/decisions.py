"""Decision persistence and retrieval using SQLAlchemy."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import ModerationDecision, ModerationJob, Status


def _decision_to_dict(decision: ModerationDecision) -> Dict[str, Any]:
    """Serialize a ModerationDecision into a plain dict."""
    return {
        "correlating_id": str(decision.correlating_id),
        "final_verdict": decision.final_verdict.value,
        "timed_out": decision.timed_out,
        "decided_at": decision.decided_at,
    }


async def upsert_decision(session: AsyncSession, payload: Dict[str, Any]) -> ModerationDecision:
    """
    Store the composite decision. Creates or updates by correlating_id.

    `payload` should include: correlating_id, final_verdict, timed_out (bool).
    """
    correlating_id = payload["correlating_id"]

    decision = await session.get(ModerationDecision, correlating_id)
    if decision:
        decision.final_verdict = payload["final_verdict"]
        decision.timed_out = payload.get("timed_out", False)
    else:
        decision = ModerationDecision(**payload)
        session.add(decision)

    # Update job lifecycle if present
    job = await session.get(ModerationJob, correlating_id)
    if job:
        job.status = Status.COMPLETED

    # Caller is responsible for committing
    return decision


async def fetch_decision(session: AsyncSession, correlating_id: str) -> Optional[Dict[str, Any]]:
    """Return a prior decision for a given job to support idempotency."""
    stmt = select(ModerationDecision).where(ModerationDecision.correlating_id == correlating_id)
    result = await session.execute(stmt)
    decision = result.scalar_one_or_none()
    if decision is None:
        return None
    return _decision_to_dict(decision)
