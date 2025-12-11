"""Use-case orchestrator for the composite text moderation flow."""

from typing import Any, Dict


async def run_text_moderation(event: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize, deduplicate, fan out to detectors, aggregate, persist, and publish."""
    raise NotImplementedError("Implement the end-to-end moderation pipeline.")
