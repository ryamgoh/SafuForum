"""Decision persistence and retrieval (to be backed by a database)."""

from typing import Any, Dict, Optional


async def upsert_decision(decision: Dict[str, Any]) -> None:
    """Store the composite decision and raw detector outputs."""
    raise NotImplementedError("Persist moderation decisions in the backing store.")


async def fetch_decision(request_id: str) -> Optional[Dict[str, Any]]:
    """Return a prior decision for a given request to support idempotency."""
    raise NotImplementedError("Load an existing decision by request identifier.")
