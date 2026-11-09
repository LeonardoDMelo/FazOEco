"""Administrative panel endpoints."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentAdmin, DbSession
from app.api.v1.helpers import (
    apply_offer_filters,
    apply_sort,
    base_offer_query,
    offer_to_list_item,
    paginate_offers,
)
from app.connectors import (
    AmazonConnector,
    MercadoLivreConnector,
    ShopeeConnector,
    run_connectors,
)
from app.core.config import get_settings
from app.core.timezone import utc_now
from app.models.log import Log
from app.models.offer import Offer
from app.models.setting import Setting
from app.schemas.admin import (
    AdminStats,
    ConnectorRunRequest,
    ConnectorRunResponse,
    ConnectorStatus,
    DiscountBandsUpdate,
    LogRead,
    RankingWeightsUpdate,
    SettingRead,
    SystemSettingsUpdate,
)
from app.schemas.offer_public import OfferAdminUpdate, OfferListItem
from app.schemas.pagination import Page

router = APIRouter(prefix="/admin", tags=["admin"])

RANKING_SETTING_KEY = "ranking_weights"
BANDS_SETTING_KEY = "discount_bands"
SYSTEM_SETTING_KEY = "system_settings"

DEFAULT_SYSTEM_SETTINGS = {
    "auto_publish_enabled": False,
    "simulation_mode_preferred": True,
    "price_revalidation_hours": 6,
    "connectors_enabled": {
        "amazon": True,
        "mercadolivre": True,
        "shopee": True,
    },
}


def _connector_map(settings=None):
    settings = settings or get_settings()
    return {
        "amazon": AmazonConnector(settings=settings),
        "mercadolivre": MercadoLivreConnector(settings=settings),
        "shopee": ShopeeConnector(settings=settings),
    }


@router.get("/stats", response_model=AdminStats)
async def admin_stats(db: DbSession, _: CurrentAdmin) -> AdminStats:
    """Métricas operacionais do painel."""
    from sqlalchemy import func

    settings = get_settings()
    connectors = _connector_map(settings)

    async def _count(*clauses) -> int:
        stmt = select(func.count()).select_from(Offer)
        for clause in clauses:
            stmt = stmt.where(clause)
        return int((await db.execute(stmt)).scalar_one())

    logs_total = int((await db.execute(select(func.count()).select_from(Log))).scalar_one())
    ready = sum(1 for c in connectors.values() if c.has_credentials() or c.simulation_enabled)

    return AdminStats(
        offers_approved=await _count(Offer.approval_status == "approved"),
        offers_pending=await _count(Offer.approval_status == "pending"),
        offers_rejected=await _count(Offer.approval_status == "rejected"),
        offers_unavailable=await _count(Offer.is_available.is_(False)),
        connectors_ready=ready,
        connectors_total=len(connectors),
        logs_total=logs_total,
        simulation_enabled=bool(settings.enable_simulation_mode),
    )


@router.get("/offers", response_model=Page[OfferListItem])
async def admin_list_offers(
    db: DbSession,
    _: CurrentAdmin,
    q: str | None = None,
    store: str | None = None,
    approval_status: str | None = Query(default=None),
    is_available: bool | None = Query(default=None),
    sort: str = Query(default="newest"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Page[OfferListItem]:
    """Lista todas as ofertas (inclui pending/rejected) para moderação."""
    stmt = base_offer_query(public_only=False)
    stmt = apply_offer_filters(
        stmt,
        q=q,
        store=store,
        approval_status=approval_status,
    )
    if is_available is not None:
        stmt = stmt.where(Offer.is_available.is_(is_available))
    stmt = apply_sort(stmt, sort)
    return await paginate_offers(db, stmt, page=page, page_size=page_size)


@router.patch("/offers/{offer_id}", response_model=OfferListItem)
async def admin_update_offer(
    offer_id: UUID,
    payload: OfferAdminUpdate,
    db: DbSession,
    admin: CurrentAdmin,
) -> OfferListItem:
    """Atualiza campos de oferta e/ou status de moderação."""
    result = await db.execute(
        base_offer_query(public_only=False).where(Offer.id == offer_id)
    )
    offer = result.scalars().unique().first()
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(offer, key, value)

    db.add(
        Log(
            level="INFO",
            source="admin.offers",
            message=f"Offer {offer_id} updated",
            context={"changes": data},
            user_id=admin.id,
        )
    )
    await db.commit()
    await db.refresh(offer)
    # reload relationship
    result = await db.execute(
        base_offer_query(public_only=False).where(Offer.id == offer_id)
    )
    offer = result.scalars().unique().one()
    return offer_to_list_item(offer)


@router.post("/offers/{offer_id}/approve", response_model=OfferListItem)
async def approve_offer(
    offer_id: UUID,
    db: DbSession,
    admin: CurrentAdmin,
) -> OfferListItem:
    return await admin_update_offer(
        offer_id,
        OfferAdminUpdate(approval_status="approved"),
        db,
        admin,
    )


@router.post("/offers/{offer_id}/reject", response_model=OfferListItem)
async def reject_offer(
    offer_id: UUID,
    db: DbSession,
    admin: CurrentAdmin,
) -> OfferListItem:
    return await admin_update_offer(
        offer_id,
        OfferAdminUpdate(approval_status="rejected"),
        db,
        admin,
    )


@router.get("/connectors", response_model=list[ConnectorStatus])
async def list_connectors(_: CurrentAdmin) -> list[ConnectorStatus]:
    """Status dos conectores autorizados."""
    settings = get_settings()
    connectors = _connector_map(settings)
    return [
        ConnectorStatus(
            store_key=key,
            store_name=connector.store_name,
            has_credentials=connector.has_credentials(),
            simulation_enabled=connector.simulation_enabled,
        )
        for key, connector in connectors.items()
    ]


@router.post("/connectors/run", response_model=ConnectorRunResponse)
async def run_store_connectors(
    payload: ConnectorRunRequest,
    db: DbSession,
    admin: CurrentAdmin,
) -> ConnectorRunResponse:
    """Dispara coleta simulada/live; falhas ficam isoladas por loja."""
    settings = get_settings()
    all_connectors = _connector_map(settings)
    selected = payload.stores or list(all_connectors.keys())
    connectors = [all_connectors[key] for key in selected if key in all_connectors]
    if not connectors:
        raise HTTPException(status_code=400, detail="No valid stores selected")

    results = await run_connectors(connectors, payload.query, limit=payload.limit)
    serialized: list[dict[str, Any]] = []
    for item in results:
        serialized.append(
            {
                "store_name": item.store_name,
                "success": item.success,
                "simulated": item.simulated,
                "error": item.error,
                "duration_ms": item.duration_ms,
                "offers_count": len(item.offers),
                "offers": [
                    {
                        "external_offer_id": o.external_offer_id,
                        "title": o.title,
                        "current_price": str(o.current_price),
                        "original_price": str(o.original_price) if o.original_price else None,
                        "affiliate_url": o.affiliate_url,
                        "gtin": o.gtin,
                        "average_rating": str(o.average_rating) if o.average_rating else None,
                        "ratings_count": o.ratings_count,
                        "sales_count": o.sales_count,
                    }
                    for o in item.offers
                ],
            }
        )

    db.add(
        Log(
            level="INFO",
            source="admin.connectors",
            message="Connector run finished",
            context={"query": payload.query, "results": serialized},
            user_id=admin.id,
            created_at=utc_now(),
        )
    )
    await db.commit()

    for connector in connectors:
        await connector.aclose()

    return ConnectorRunResponse(results=serialized)


async def _upsert_setting(
    db: DbSession,
    *,
    key: str,
    value: Any,
    description: str,
) -> Setting:
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = Setting(key=key, value=value, description=description)
        db.add(setting)
    else:
        setting.value = value
        setting.description = description
    await db.commit()
    await db.refresh(setting)
    return setting


@router.get("/settings/ranking", response_model=SettingRead)
async def get_ranking_weights(db: DbSession, _: CurrentAdmin) -> SettingRead:
    result = await db.execute(select(Setting).where(Setting.key == RANKING_SETTING_KEY))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = await _upsert_setting(
            db,
            key=RANKING_SETTING_KEY,
            value={
                "discount": "30",
                "rating": "25",
                "sales": "20",
                "reviews": "15",
                "engagement": "10",
            },
            description="Pesos do RankingService (5 pilares)",
        )
    return SettingRead.model_validate(setting)


@router.put("/settings/ranking", response_model=SettingRead)
async def update_ranking_weights(
    payload: RankingWeightsUpdate,
    db: DbSession,
    admin: CurrentAdmin,
) -> SettingRead:
    setting = await _upsert_setting(
        db,
        key=RANKING_SETTING_KEY,
        value={k: str(v) for k, v in payload.model_dump().items()},
        description="Pesos do RankingService (5 pilares)",
    )
    db.add(
        Log(
            level="INFO",
            source="admin.settings",
            message="Ranking weights updated",
            context=payload.model_dump(mode="json"),
            user_id=admin.id,
        )
    )
    await db.commit()
    await db.refresh(setting)
    return SettingRead.model_validate(setting)


@router.get("/settings/discount-bands", response_model=SettingRead)
async def get_discount_bands(db: DbSession, _: CurrentAdmin) -> SettingRead:
    result = await db.execute(select(Setting).where(Setting.key == BANDS_SETTING_KEY))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = await _upsert_setting(
            db,
            key=BANDS_SETTING_KEY,
            value={
                "min_discount_percent": "5.00",
                "max_discount_percent": "90.00",
                "bands": [
                    {"name": "none", "min": "0", "max": "5"},
                    {"name": "low", "min": "5", "max": "15"},
                    {"name": "medium", "min": "15", "max": "30"},
                    {"name": "high", "min": "30", "max": "50"},
                    {"name": "extreme", "min": "50", "max": None},
                ],
            },
            description="Faixas dinâmicas e critérios do PricingService",
        )
    return SettingRead.model_validate(setting)


@router.put("/settings/discount-bands", response_model=SettingRead)
async def update_discount_bands(
    payload: DiscountBandsUpdate,
    db: DbSession,
    admin: CurrentAdmin,
) -> SettingRead:
    if payload.min_discount_percent > payload.max_discount_percent:
        raise HTTPException(status_code=400, detail="min_discount cannot exceed max_discount")
    setting = await _upsert_setting(
        db,
        key=BANDS_SETTING_KEY,
        value={
            "min_discount_percent": str(payload.min_discount_percent),
            "max_discount_percent": str(payload.max_discount_percent),
            "bands": payload.bands,
        },
        description="Faixas dinâmicas e critérios do PricingService",
    )
    db.add(
        Log(
            level="INFO",
            source="admin.settings",
            message="Discount bands updated",
            context=payload.model_dump(mode="json"),
            user_id=admin.id,
        )
    )
    await db.commit()
    await db.refresh(setting)
    return SettingRead.model_validate(setting)


@router.get("/settings/system", response_model=SettingRead)
async def get_system_settings(db: DbSession, _: CurrentAdmin) -> SettingRead:
    result = await db.execute(select(Setting).where(Setting.key == SYSTEM_SETTING_KEY))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = await _upsert_setting(
            db,
            key=SYSTEM_SETTING_KEY,
            value=DEFAULT_SYSTEM_SETTINGS,
            description="Configurações operacionais do painel (auto-publish, conectores, revalidação)",
        )
    return SettingRead.model_validate(setting)


@router.put("/settings/system", response_model=SettingRead)
async def update_system_settings(
    payload: SystemSettingsUpdate,
    db: DbSession,
    admin: CurrentAdmin,
) -> SettingRead:
    setting = await _upsert_setting(
        db,
        key=SYSTEM_SETTING_KEY,
        value=payload.model_dump(),
        description="Configurações operacionais do painel (auto-publish, conectores, revalidação)",
    )
    db.add(
        Log(
            level="INFO",
            source="admin.settings",
            message="System settings updated",
            context=payload.model_dump(mode="json"),
            user_id=admin.id,
        )
    )
    await db.commit()
    await db.refresh(setting)
    return SettingRead.model_validate(setting)


@router.get("/logs", response_model=Page[LogRead])
async def list_logs(
    db: DbSession,
    _: CurrentAdmin,
    source: str | None = None,
    level: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Page[LogRead]:
    """Logs de execução / auditoria do painel."""
    from sqlalchemy import func

    from app.schemas.pagination import PageMeta

    stmt = select(Log)
    if source:
        stmt = stmt.where(Log.source == source)
    if level:
        stmt = stmt.where(Log.level == level.upper())

    total = int(
        (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    )
    pages = (total + page_size - 1) // page_size if total else 0
    rows = (
        await db.execute(
            stmt.order_by(Log.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()

    return Page(
        items=[LogRead.model_validate(row) for row in rows],
        meta=PageMeta(page=page, page_size=page_size, total=total, pages=pages),
    )
