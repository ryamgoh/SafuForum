"""Orchestrator flow."""

from typing import Any, Dict


async def run_orchestrator(event: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize, deduplicate, fan out to detectors, aggregate, persist, and publish."""
    raise NotImplementedError("Implement the end-to-end moderation pipeline.")
