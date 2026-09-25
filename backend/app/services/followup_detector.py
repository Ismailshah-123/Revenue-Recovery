# ====================== app/services/followup_detector.py ======================
"""
Lightweight keyword-based heuristic for flagging emails that likely need
a follow-up, with a confidence score used to prioritize the queue.
"""
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("followup_detector")

KEYWORDS: Dict[str, float] = {
    "what's next": 0.15,
    "next steps": 0.15,
    "follow up": 0.2,
    "urgent": 0.25,
    "asap": 0.25,
    "response needed": 0.2,
    "action required": 0.2,
    "please respond": 0.15,
    "waiting for": 0.1,
    "any update": 0.1,
}

URGENCY_THRESHOLDS: Dict[str, float] = {
    "low": 0.0,
    "medium": 0.25,
    "high": 0.5,
}


def detect_followups(snippet: str) -> Tuple[bool, float]:
    """Returns (needs_followup, confidence 0-1) based on keyword hits."""
    if not snippet.strip():
        return False, 0.0

    text = snippet.lower()
    hits: List[str] = [k for k in KEYWORDS if k in text]

    if not hits:
        return False, 0.0

    confidence = min(0.95, sum(KEYWORDS[k] for k in hits))
    logger.debug("Detected keywords=%s confidence=%.2f", hits, confidence)
    return True, confidence


def determine_urgency(confidence: float) -> str:
    """Maps a confidence score to an urgency label (low, medium, high)."""
    if confidence >= URGENCY_THRESHOLDS["high"]:
        return "high"
    if confidence >= URGENCY_THRESHOLDS["medium"]:
        return "medium"
    return "low"
