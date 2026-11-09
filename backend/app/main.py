"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.security import RateLimitMiddleware, SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan hooks (startup / shutdown)."""
    from app.core.bootstrap import ensure_initial_admin
    from app.scheduler.manager import get_scheduler_manager

    from app.core.config import get_settings

    await ensure_initial_admin()
    settings = get_settings()
    scheduler = get_scheduler_manager()
    if settings.run_scheduler:
        scheduler.start()
    try:
        yield
    finally:
        if settings.run_scheduler:
            scheduler.shutdown()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        openapi_url="/openapi.json" if settings.app_env != "production" else None,
    )

    # CORS: origins come exclusively from BACKEND_CORS_ORIGINS (no wildcard in prod).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
    )
    # Middleware stack: last added runs first on request.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)

    app.include_router(api_router, prefix="/api")

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": f"{settings.app_name} API", "env": settings.app_env}

    return app


app = create_app()
