"""Router collection for the TextModerationService HTTP surface."""

from routers.health import router as health_router
from routers.moderations import router as moderations_router

__all__ = ["health_router", "moderations_router"]
