"""Shared Pydantic helpers."""

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base schema with ORM mode enabled."""

    model_config = ConfigDict(from_attributes=True)
