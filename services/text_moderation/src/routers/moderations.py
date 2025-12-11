"""Placeholder HTTP endpoints for ad-hoc moderation requests."""

from fastapi import APIRouter, Depends
from middlewares.auth import get_current_user

router = APIRouter(
    prefix="/moderations",
    tags=["moderations"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/", summary="Run text moderation on-demand")
async def create_moderation():  # pragma: no cover - placeholder
    """Accept raw text or S3 URI, kick off moderation, and return a decision."""
    raise NotImplementedError("Expose synchronous moderation endpoint.")

@router.get("/getprotectedresource", summary="Get protected resource example")
async def get_protected_resource(
    current_user: dict = Depends(get_current_user)
):
    """An example endpoint that requires authentication and returns user info."""
    return {"message": "This is a protected resource", "user": current_user}
