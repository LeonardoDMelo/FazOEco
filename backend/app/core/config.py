"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Annotated, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized runtime configuration (Pydantic v2)."""

    model_config = SettingsConfigDict(
        # Aceita .env na pasta backend/ ou na raiz do monorepo
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="FazOEco", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")

    database_url: str = Field(
        default="postgresql+asyncpg://fazoeeco:fazoeeco_secret@localhost:5432/fazoeeco",
        alias="DATABASE_URL",
    )

    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    # NoDecode: evita parse JSON automático; aceita CSV do .env
    backend_cors_origins: Annotated[List[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="BACKEND_CORS_ORIGINS",
    )
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60 * 24,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    display_timezone: str = Field(
        default="America/Sao_Paulo",
        alias="DISPLAY_TIMEZONE",
    )

    # --- Connectors / simulation ---
    enable_simulation_mode: bool = Field(default=True, alias="ENABLE_SIMULATION_MODE")

    amazon_access_key: str | None = Field(default=None, alias="AMAZON_ACCESS_KEY")
    amazon_secret_key: str | None = Field(default=None, alias="AMAZON_SECRET_KEY")
    amazon_partner_tag: str | None = Field(default=None, alias="AMAZON_PARTNER_TAG")

    mercadolivre_site_id: str = Field(default="MLB", alias="MERCADOLIVRE_SITE_ID")
    mercadolivre_access_token: str | None = Field(
        default=None, alias="MERCADOLIVRE_ACCESS_TOKEN"
    )
    mercadolivre_affiliate_id: str | None = Field(
        default=None, alias="MERCADOLIVRE_AFFILIATE_ID"
    )

    shopee_partner_id: str | None = Field(default=None, alias="SHOPEE_PARTNER_ID")
    shopee_partner_key: str | None = Field(default=None, alias="SHOPEE_PARTNER_KEY")
    shopee_shop_id: str | None = Field(default=None, alias="SHOPEE_SHOP_ID")

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
