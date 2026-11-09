"""Public category endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.category import Category
from app.schemas.category import CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
async def list_categories(db: DbSession) -> list[Category]:
    """Lista categorias ativas (árvore plana com parent_id)."""
    result = await db.execute(
        select(Category)
        .where(Category.is_active.is_(True))
        .order_by(Category.name.asc())
    )
    return list(result.scalars().all())


@router.get("/{slug}", response_model=CategoryRead)
async def get_category(slug: str, db: DbSession) -> Category:
    """Detalhe de categoria por slug."""
    result = await db.execute(
        select(Category).where(
            Category.slug == slug.strip().lower(),
            Category.is_active.is_(True),
        )
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category
