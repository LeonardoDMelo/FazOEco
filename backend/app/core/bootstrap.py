"""Startup bootstrap helpers (initial admin user, etc.)."""

from __future__ import annotations

import logging

from sqlalchemy import or_, select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User

logger = logging.getLogger(__name__)


async def ensure_initial_admin() -> None:
    """Create or refresh the bootstrap admin from ADMIN_INITIAL_* env vars."""
    settings = get_settings()
    email = settings.admin_initial_email.strip().lower()
    username = settings.admin_initial_username.strip()
    password = settings.admin_initial_password

    if not email or not username or not password:
        logger.warning("Skipping admin bootstrap: incomplete ADMIN_INITIAL_* settings")
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(or_(User.email == email, User.username == username))
        )
        user = result.scalar_one_or_none()
        if user is None:
            db.add(
                User(
                    email=email,
                    username=username,
                    hashed_password=hash_password(password),
                    full_name="Administrador",
                    is_active=True,
                    is_superuser=True,
                )
            )
            await db.commit()
            logger.info("Initial admin created: %s", email)
            return

        # Keep bootstrap credentials in sync for local/dev convenience
        user.email = email
        user.username = username
        user.hashed_password = hash_password(password)
        user.is_active = True
        user.is_superuser = True
        await db.commit()
        logger.info("Initial admin credentials refreshed: %s", email)
