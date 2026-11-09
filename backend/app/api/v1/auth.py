"""Admin authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import (
    clear_auth_cookie,
    create_access_token,
    set_auth_cookie,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import Token, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def _cookie_is_secure(request: Request) -> bool:
    settings = get_settings()
    forwarded = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    if forwarded == "https" or request.url.scheme == "https":
        return True
    return settings.app_env == "production"


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    db: DbSession,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """OAuth2 password flow — username can be username or email."""
    result = await db.execute(
        select(User).where(
            (User.username == form_data.username) | (User.email == form_data.username)
        )
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    settings = get_settings()
    token = create_access_token(
        user.id,
        extra_claims={"username": user.username, "is_superuser": user.is_superuser},
    )
    set_auth_cookie(
        response,
        token,
        secure=_cookie_is_secure(request),
        max_age=settings.access_token_expire_minutes * 60,
    )
    return Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """Clear the HttpOnly session cookie."""
    clear_auth_cookie(response)


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser) -> User:
    """Return the authenticated user profile."""
    return current_user
