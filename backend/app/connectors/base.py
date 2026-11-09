"""Abstract async connector interface with resilience helpers."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Sequence

import httpx

from app.connectors.mock_data import get_mock_offers
from app.core.config import Settings, get_settings
from app.core.timezone import utc_now

logger = logging.getLogger(__name__)


class ConnectorError(Exception):
    """Raised when a connector cannot complete a fetch."""

    def __init__(self, store: str, message: str, *, retriable: bool = False) -> None:
        self.store = store
        self.retriable = retriable
        super().__init__(f"[{store}] {message}")


@dataclass(frozen=True, slots=True)
class NormalizedOffer:
    """Store-agnostic offer payload collected by connectors."""

    store_name: str
    affiliate_network: str
    external_offer_id: str
    title: str
    affiliate_url: str
    current_price: Decimal
    original_price: Decimal | None
    currency: str = "BRL"
    gtin: str | None = None
    brand: str | None = None
    image_url: str | None = None
    average_rating: Decimal | None = None
    ratings_count: int = 0
    reviews_count: int = 0
    sales_count: int | None = None
    is_available: bool = True
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ConnectorResult:
    """Per-connector execution outcome (success or isolated failure)."""

    store_name: str
    success: bool
    offers: tuple[NormalizedOffer, ...] = ()
    error: str | None = None
    simulated: bool = False
    duration_ms: int = 0


class BaseConnector(ABC):
    """Base class for authorized marketplace connectors."""

    store_key: str
    store_name: str
    affiliate_network: str
    base_url: str

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.settings = settings or get_settings()
        self.timeout = timeout
        self._client = client
        self._owns_client = client is None

    @property
    def simulation_enabled(self) -> bool:
        return bool(self.settings.enable_simulation_mode)

    @abstractmethod
    def has_credentials(self) -> bool:
        """Return True when live API credentials are configured."""

    @abstractmethod
    async def _fetch_live(self, query: str, *, limit: int) -> list[NormalizedOffer]:
        """Call the real marketplace API and normalize results."""

    def _from_mock_item(self, item: dict[str, Any]) -> NormalizedOffer:
        return NormalizedOffer(
            store_name=self.store_name,
            affiliate_network=self.affiliate_network,
            external_offer_id=str(item["external_offer_id"]),
            title=str(item["title"]),
            affiliate_url=str(item["affiliate_url"]),
            current_price=Decimal(str(item["current_price"])),
            original_price=(
                Decimal(str(item["original_price"]))
                if item.get("original_price") is not None
                else None
            ),
            currency=str(item.get("currency") or "BRL"),
            gtin=item.get("gtin"),
            brand=item.get("brand"),
            image_url=item.get("image_url"),
            average_rating=(
                Decimal(str(item["average_rating"]))
                if item.get("average_rating") is not None
                else None
            ),
            ratings_count=int(item.get("ratings_count") or 0),
            reviews_count=int(item.get("reviews_count") or 0),
            sales_count=(
                int(item["sales_count"]) if item.get("sales_count") is not None else None
            ),
            is_available=bool(item.get("is_available", True)),
            raw=dict(item),
        )

    async def _fetch_simulated(self, query: str, *, limit: int) -> list[NormalizedOffer]:
        items = get_mock_offers(self.store_key, query)[:limit]
        return [self._from_mock_item(item) for item in items]

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            from app.services.http_client import assert_url_safe

            # Validate connector base URL once (SSRF allowlist).
            assert_url_safe(self.base_url.rstrip("/") + "/", resolve_dns=False)

            async def _ssrf_request_hook(request: httpx.Request) -> None:
                assert_url_safe(str(request.url), resolve_dns=True)

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._default_headers(),
                follow_redirects=False,
                event_hooks={"request": [_ssrf_request_hook]},
            )
        return self._client

    def _default_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "User-Agent": f"{self.settings.app_name}/1.0 (+connectors)",
        }

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Authenticated HTTP call with unified error mapping."""
        client = await self._get_client()
        try:
            response = await client.request(
                method,
                path,
                params=params,
                json=json,
                headers=headers,
            )
        except httpx.TimeoutException as exc:
            raise ConnectorError(self.store_name, "request timeout", retriable=True) from exc
        except ValueError as exc:
            # SSRFError inherits ValueError — do not retry blocked destinations.
            raise ConnectorError(self.store_name, f"ssrf blocked: {exc}", retriable=False) from exc
        except httpx.HTTPError as exc:
            raise ConnectorError(self.store_name, f"http error: {exc}", retriable=True) from exc

        if response.status_code in {401, 403}:
            raise ConnectorError(
                self.store_name,
                f"authentication failed ({response.status_code})",
                retriable=False,
            )
        if response.status_code >= 500:
            raise ConnectorError(
                self.store_name,
                f"upstream error ({response.status_code})",
                retriable=True,
            )
        if response.status_code >= 400:
            raise ConnectorError(
                self.store_name,
                f"client error ({response.status_code}): {response.text[:200]}",
                retriable=False,
            )
        return response

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch_offers(self, query: str = "", *, limit: int = 20) -> ConnectorResult:
        """
        Execute a resilient fetch:
        - simulation mode → mock data
        - missing credentials → soft skip (success=False, isolated)
        - live API errors → captured without raising to the caller
        """
        started = utc_now()
        simulated = False

        try:
            if self.simulation_enabled:
                simulated = True
                offers = await self._fetch_simulated(query, limit=limit)
                logger.info(
                    "connector.simulation store=%s query=%r count=%s",
                    self.store_name,
                    query,
                    len(offers),
                )
            elif not self.has_credentials():
                raise ConnectorError(
                    self.store_name,
                    "credentials not configured; skipping live fetch",
                    retriable=False,
                )
            else:
                offers = await self._fetch_live(query, limit=limit)
                logger.info(
                    "connector.live store=%s query=%r count=%s",
                    self.store_name,
                    query,
                    len(offers),
                )

            elapsed = int((utc_now() - started).total_seconds() * 1000)
            return ConnectorResult(
                store_name=self.store_name,
                success=True,
                offers=tuple(offers),
                simulated=simulated,
                duration_ms=elapsed,
            )
        except ConnectorError as exc:
            elapsed = int((utc_now() - started).total_seconds() * 1000)
            logger.warning(
                "connector.failed store=%s error=%s retriable=%s",
                self.store_name,
                str(exc),
                exc.retriable,
            )
            return ConnectorResult(
                store_name=self.store_name,
                success=False,
                error=str(exc),
                simulated=simulated,
                duration_ms=elapsed,
            )
        except Exception as exc:  # noqa: BLE001 — isolate unexpected failures
            elapsed = int((utc_now() - started).total_seconds() * 1000)
            logger.exception("connector.unexpected store=%s", self.store_name)
            return ConnectorResult(
                store_name=self.store_name,
                success=False,
                error=f"[{self.store_name}] unexpected: {exc}",
                simulated=simulated,
                duration_ms=elapsed,
            )


async def run_connectors(
    connectors: Sequence[BaseConnector],
    query: str = "",
    *,
    limit: int = 20,
) -> list[ConnectorResult]:
    """Run connectors concurrently; failures stay isolated per store."""
    tasks = [connector.fetch_offers(query, limit=limit) for connector in connectors]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return list(results)
