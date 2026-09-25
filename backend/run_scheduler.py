# run_scheduler.py
"""
Standalone entrypoint for running the email pipeline scheduler as its own
process, separate from the API server -- useful if you deploy the API and
the background worker independently.

If you run the API server (app.main:app) with MVP_MODE=false, it already
starts this same scheduler in-process on startup (see app/main.py's
lifespan). Don't run both at once against the same database, or emails
will be processed twice.

The original version called start_scheduler() and then blocked with a
plain `while True: time.sleep(10)`. AsyncIOScheduler relies on an asyncio
event loop actually being run to fire its jobs; time.sleep() in a
synchronous loop never gives the loop a chance to run, so the scheduler
would start but its jobs would never execute. This version drives the
loop properly.
"""
import asyncio
import logging

from app.tasks.scheduler import shutdown_scheduler, start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("run_scheduler")


async def main() -> None:
    start_scheduler()
    logger.info("Scheduler running. Press Ctrl+C to stop.")
    try:
        # Keep the event loop alive so APScheduler's jobs can fire.
        await asyncio.Event().wait()
    finally:
        shutdown_scheduler()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down.")
