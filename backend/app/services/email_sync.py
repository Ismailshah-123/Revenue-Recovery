# ====================== app/services/email_sync.py ======================
"""
Gmail ingestion layer. Reads a locally stored OAuth token (token.pickle,
generated once via a Gmail OAuth consent flow -- see README) and pulls
recent message threads. Returns an empty list -- never raises -- whenever
Gmail isn't configured yet, so the rest of the app keeps working in a
"no inbox connected" state instead of crashing.
"""
import asyncio
import logging
import pickle
import time
from pathlib import Path
from typing import Dict, List

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger("email_sync")

# Resolved relative to the backend/ package root, not the process's
# current working directory, so this works regardless of where
# `uvicorn` (or pytest) is launched from.
TOKEN_PATH = Path(__file__).resolve().parents[2] / "token.pickle"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def _fetch_threads_sync(max_threads: int) -> List[Dict]:
    """Synchronous Gmail API call. Returns a list of {thread_id, snippet} dicts."""
    if not TOKEN_PATH.exists():
        logger.warning("Gmail token missing at %s -- running with no inbox connected", TOKEN_PATH)
        return []

    try:
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

        service = build("gmail", "v1", credentials=creds)

        results = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                results = service.users().messages().list(userId="me", maxResults=max_threads).execute()
                break
            except HttpError as e:
                logger.warning("Gmail list attempt %d/%d failed: %s", attempt, MAX_RETRIES, e)
                if attempt == MAX_RETRIES:
                    raise
                time.sleep(RETRY_DELAY)

        if results is None:
            return []

        messages = results.get("messages", [])
        threads = []

        for msg in messages:
            full = {}
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    full = service.users().messages().get(userId="me", id=msg["id"]).execute()
                    break
                except HttpError as e:
                    logger.warning("Gmail message fetch attempt %d/%d failed: %s", attempt, MAX_RETRIES, e)
                    if attempt == MAX_RETRIES:
                        logger.error("Skipping message id=%s after repeated failures", msg["id"])
                        full = {}
                    else:
                        time.sleep(RETRY_DELAY)

            thread_id = full.get("threadId")
            if thread_id:
                threads.append({"thread_id": thread_id, "snippet": full.get("snippet", "")})

        unique_threads = list({t["thread_id"]: t for t in threads}.values())
        logger.info("Fetched %d unique Gmail threads", len(unique_threads))
        return unique_threads

    except Exception:
        logger.exception("Failed to fetch Gmail threads")
        return []


async def fetch_email_threads(max_threads: int = 20) -> List[Dict]:
    """Async wrapper around the blocking Gmail client, off the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _fetch_threads_sync, max_threads)
