"""Admin endpoints to inspect and manually trigger scheduler jobs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.api.deps import CurrentAdmin, DbSession
from app.core.timezone import utc_now
from app.models.log import Log
from app.scheduler.jobs import run_deal_ingestion_job, run_deal_revalidation_job
from app.scheduler.manager import get_scheduler_manager

router = APIRouter(prefix="/admin/jobs", tags=["admin-jobs"])


class JobTriggerResponse(BaseModel):
    accepted: bool = True
    job: str
    mode: str = Field(description="async|sync")
    result: dict[str, Any] | None = None


class JobStatusResponse(BaseModel):
    running: bool
    jobs: list[dict[str, Any]]


@router.get("/status", response_model=JobStatusResponse)
async def jobs_status(_: CurrentAdmin) -> JobStatusResponse:
    status = get_scheduler_manager().status()
    return JobStatusResponse(**status)


@router.post("/trigger-ingestion", response_model=JobTriggerResponse)
async def trigger_ingestion(
    db: DbSession,
    admin: CurrentAdmin,
    background_tasks: BackgroundTasks,
    query: str = Query(default="ofertas", max_length=120),
    wait: bool = Query(default=False, description="If true, run inline and return summary"),
) -> JobTriggerResponse:
    """Manually trigger the deal ingestion job."""
    db.add(
        Log(
            level="INFO",
            source="admin.jobs",
            message="Manual ingestion trigger",
            context={"query": query, "wait": wait},
            user_id=admin.id,
            created_at=utc_now(),
        )
    )
    await db.commit()

    if wait:
        result = await run_deal_ingestion_job(query=query)
        return JobTriggerResponse(job="ingestion", mode="sync", result=result)

    background_tasks.add_task(run_deal_ingestion_job, query)
    return JobTriggerResponse(job="ingestion", mode="async")


@router.post("/trigger-revalidation", response_model=JobTriggerResponse)
async def trigger_revalidation(
    db: DbSession,
    admin: CurrentAdmin,
    background_tasks: BackgroundTasks,
    wait: bool = Query(default=False),
) -> JobTriggerResponse:
    """Manually trigger the revalidation/expiration job."""
    db.add(
        Log(
            level="INFO",
            source="admin.jobs",
            message="Manual revalidation trigger",
            context={"wait": wait},
            user_id=admin.id,
            created_at=utc_now(),
        )
    )
    await db.commit()

    if wait:
        result = await run_deal_revalidation_job()
        return JobTriggerResponse(job="revalidation", mode="sync", result=result)

    background_tasks.add_task(run_deal_revalidation_job)
    return JobTriggerResponse(job="revalidation", mode="async")
