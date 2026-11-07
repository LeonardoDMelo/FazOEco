"""Pydantic v2 schemas package."""

from app.schemas.category import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
)
from app.schemas.offer import OfferCreate, OfferRead, OfferUpdate
from app.schemas.price_history import PriceHistoryCreate, PriceHistoryRead
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.schemas.setting import SettingCreate, SettingRead, SettingUpdate

__all__ = [
    "CategoryCreate",
    "CategoryRead",
    "CategoryUpdate",
    "OfferCreate",
    "OfferRead",
    "OfferUpdate",
    "PriceHistoryCreate",
    "PriceHistoryRead",
    "ProductCreate",
    "ProductRead",
    "ProductUpdate",
    "SettingCreate",
    "SettingRead",
    "SettingUpdate",
]
