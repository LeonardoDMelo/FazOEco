"""Root API router."""

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Liveness probe for the API."""
    return {"status": "ok"}
