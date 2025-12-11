from fastapi import FastAPI

from routers import health_router, moderations_router

app = FastAPI(title="Text Moderation Service")
app.include_router(health_router)
app.include_router(moderations_router)
