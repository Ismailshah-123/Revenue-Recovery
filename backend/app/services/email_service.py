# ====================== app/services/email_service.py ======================
"""
Turns raw Gmail thread dicts into stored, AI-enriched EmailThread rows:
heuristic follow-up detection, AI enrichment, revenue estimation, persistence.
"""
import asyncio
import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.services.ai_service import generate_insights
from app.services.email_sync import fetch_email_threads
from app.services.followup_detector import detect_followups

logger = logging.getLogger("email_service")


async def process_email(db: AsyncSession, workspace_id: int, email: dict) -> Optional[schemas.EmailThreadResponse]:
    """Processes a single raw email dict into a stored EmailThread, or returns the existing one."""
    thread_id = email.get("thread_id")
    if not thread_id:
        logger.warning("Skipping email without thread_id: %s", email)
        return None

    existing = await crud.get_email_by_thread(db, workspace_id, thread_id)
    if existing:
        return existing

    snippet = email.get("snippet", "")
    needs_followup, heuristic_score = detect_followups(snippet)

    try:
        ai_insight = await generate_insights(snippet, thread_id)
    except Exception:
        logger.exception("AI enrichment failed for thread_id=%s", thread_id)
        ai_insight = {
            "summary": snippet[:120],
            "reasoning": "AI failed; fallback applied.",
            "suggested_action": "review",
            "sentiment": "neutral",
            "detected_value": 3000,
            "recovered_value": 0,
            "confidence_score": 0.5,
        }

    detected_value = max(int(ai_insight.get("detected_value", 3000)), int(heuristic_score * 3000))

    email_payload = {
        "thread_id": thread_id,
        "subject": email.get("subject"),
        "sender": email.get("sender"),
        "snippet": snippet,
        "needs_followup": needs_followup,
        "ai_insight": ai_insight.get("reasoning"),
        "status": "missed" if needs_followup else "logged",
        "detected_value": detected_value,
    }

    payload_schema = schemas.EmailThreadCreate(**email_payload)
    saved_email = await crud.create_email(db, workspace_id, payload_schema.model_dump())

    logger.info(
        "workspace=%s thread=%s value=$%s needs_followup=%s",
        workspace_id, thread_id, detected_value, needs_followup,
    )
    return saved_email


async def sync_emails(db: AsyncSession, workspace_id: int, limit: int = 20) -> List[schemas.EmailThreadResponse]:
    """Fetches the latest email threads from Gmail and processes each one concurrently."""
    threads = await fetch_email_threads(limit)

    if not threads:
        logger.warning("No emails fetched for workspace=%s", workspace_id)
        return []

    tasks = [process_email(db, workspace_id, t) for t in threads]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful_emails = [r for r in results if r and not isinstance(r, Exception)]
    logger.info(
        "Processed %d/%d emails for workspace=%s",
        len(successful_emails), len(threads), workspace_id,
    )
    return successful_emails
