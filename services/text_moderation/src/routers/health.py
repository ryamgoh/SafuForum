"""Basic health endpoint to verify the service is running."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service liveness probe")
async def health() -> dict[str, str]:  # pragma: no cover - trivial
    """Return a simple liveness payload."""
    return {"status": "ok"}
