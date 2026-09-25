# ====================== app/tasks/scheduler.py ======================
"""
Background email pipeline scheduler: periodically syncs and analyzes
emails for every active workspace. Fault-tolerant -- one workspace's
failure is logged and does not stop the others.
"""
import asyncio
import logging
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.future import select

from app import models
from app.database import AsyncSessionLocal
from app.services.email_service import process_email
from app.services.email_sync import fetch_email_threads

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler(timezone="UTC")


async def _process_workspace(workspace: models.Workspace, email_limit: int = 20) -> None:
    logger.info("[pipeline] workspace=%s started", workspace.id)

    async with AsyncSessionLocal() as db:
        try:
            threads = await fetch_email_threads(email_limit)
            if not threads:
                logger.info("[pipeline] no emails fetched | workspace=%s", workspace.id)
                return

            tasks = [process_email(db, workspace.id, email) for email in threads]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for r in results:
                if isinstance(r, Exception):
                    logger.exception("[pipeline] email processing failed | workspace=%s", workspace.id)
                else:
                    logger.info("[pipeline] email processed | workspace=%s thread=%s", workspace.id, r.thread_id)

        except Exception:
            logger.exception("[pipeline] workspace=%s crashed", workspace.id)

    logger.info("[pipeline] workspace=%s finished", workspace.id)


async def email_pipeline_job() -> None:
    """Runs the email pipeline across every active workspace. Fault-tolerant."""
    logger.info("[pipeline] job started")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.Workspace).where(models.Workspace.is_active.is_(True)))
        workspaces: List[models.Workspace] = list(result.scalars().all())

    if not workspaces:
        logger.info("[pipeline] no active workspaces found")
        return

    await asyncio.gather(*[_process_workspace(ws) for ws in workspaces], return_exceptions=True)
    logger.info("[pipeline] job finished")


def start_scheduler(interval_minutes: int = 5) -> None:
    """Starts the recurring email pipeline job. Safe to call more than once."""
    if scheduler.get_job("email_pipeline"):
        logger.warning("[scheduler] job already running")
        return

    scheduler.add_job(
        email_pipeline_job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="email_pipeline",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120,
    )
    scheduler.start()
    logger.info("[scheduler] started | interval=%s min", interval_minutes)


def shutdown_scheduler() -> None:
    """Gracefully stops the scheduler, if running."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[scheduler] stopped")
