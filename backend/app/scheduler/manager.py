"""APScheduler AsyncIO lifecycle manager."""

from __future__ import annotations

import logging
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_manager: "SchedulerManager | None" = None


class SchedulerManager:
    """Owns the AsyncIOScheduler instance and registered jobs."""

    def __init__(self) -> None:
        settings = get_settings()
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.ingestion_interval_minutes = settings.scheduler_ingestion_interval_minutes
        self.revalidation_interval_minutes = (
            settings.scheduler_revalidation_interval_minutes
        )
        self._started = False

    def configure_jobs(self) -> None:
        from app.scheduler.jobs import run_deal_ingestion_job, run_deal_revalidation_job

        self.scheduler.add_job(
            run_deal_ingestion_job,
            trigger=IntervalTrigger(minutes=self.ingestion_interval_minutes),
            id="deal_ingestion",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=120,
        )
        self.scheduler.add_job(
            run_deal_revalidation_job,
            trigger=IntervalTrigger(minutes=self.revalidation_interval_minutes),
            id="deal_revalidation",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=120,
        )
        logger.info(
            "Scheduler jobs configured ingestion=%sm revalidation=%sm",
            self.ingestion_interval_minutes,
            self.revalidation_interval_minutes,
        )

    def start(self) -> None:
        if self._started:
            return
        self.configure_jobs()
        self.scheduler.start()
        self._started = True
        logger.info("AsyncIOScheduler started")

    def shutdown(self) -> None:
        if not self._started:
            return
        self.scheduler.shutdown(wait=False)
        self._started = False
        logger.info("AsyncIOScheduler stopped")

    def status(self) -> dict[str, Any]:
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "next_run_time": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                    "trigger": str(job.trigger),
                }
            )
        return {"running": self._started, "jobs": jobs}


def get_scheduler_manager() -> SchedulerManager:
    global _manager
    if _manager is None:
        _manager = SchedulerManager()
    return _manager
