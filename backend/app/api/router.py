"""Root API router unifying health + v1."""

from fastapi import APIRouter

from app.api.v1 import admin, auth, categories, jobs, offers

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Liveness probe for the API."""
    return {"status": "ok"}


api_router.include_router(auth.router, prefix="/v1")
api_router.include_router(offers.router, prefix="/v1")
api_router.include_router(categories.router, prefix="/v1")
api_router.include_router(admin.router, prefix="/v1")
api_router.include_router(jobs.router, prefix="/v1")
