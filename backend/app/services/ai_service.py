# ====================== app/services/ai_service.py ======================
"""
Thread-level caching wrapper around ai_reasoning.analyze_email_with_ai,
with a human-friendly reasoning string and a revenue-recovery estimate.
"""
import asyncio
import logging
from typing import Dict, Optional

from app.services.ai_reasoning import EmailInsights, analyze_email_with_ai

logger = logging.getLogger("ai_service")

_CACHE: Dict[str, dict] = {}
_CACHE_LIMIT = 1000  # Max threads to cache in memory

_RECOMMENDATION_MAP = {
    "follow-up": "Send a follow-up to maximize recovery.",
    "reply": "Reply promptly.",
    "review": "Review carefully before action.",
    "ignore": "No immediate action required.",
}


async def generate_insights(text: str, thread_id: Optional[str] = None) -> dict:
    """
    Generate AI-driven insights for an email. Always returns a dict with
    summary, reasoning, recommendation, sentiment, detected/recovered
    value and a confidence score -- even if the AI call fails.
    """
    if not text.strip():
        return {
            "summary": "No content",
            "reasoning": "No text was provided for analysis.",
            "recommendation": "Ignore or review manually.",
            "sentiment": "neutral",
            "suggested_action": "ignore",
            "detected_value": 0,
            "recovered_value": 0,
            "confidence_score": 0.0,
        }

    if thread_id and thread_id in _CACHE:
        return _CACHE[thread_id]

    loop = asyncio.get_running_loop()
    try:
        ai_result: EmailInsights = await loop.run_in_executor(None, analyze_email_with_ai, text)
    except Exception:
        logger.exception("AI reasoning failed for thread_id=%s", thread_id)
        ai_result = {
            "summary": text[:120],
            "sentiment": "neutral",
            "urgency": "medium",
            "revenue_signal": "possible",
            "reasoning": "Fallback: AI failed to analyze email.",
            "suggested_action": "review",
            "detected_value": 5000,
            "confidence_score": 0.5,
        }

    reasoning = (
        f"Email sentiment detected as '{ai_result['sentiment']}' "
        f"with confidence {ai_result['confidence_score'] * 100:.1f}%. "
        f"Urgency: {ai_result.get('urgency', 'medium')}. "
        f"Revenue signal: {ai_result.get('revenue_signal', 'possible')}."
    )
    recommendation = _RECOMMENDATION_MAP.get(ai_result.get("suggested_action", "review"), "Review manually.")

    detected_value = ai_result.get("detected_value", 5000)
    recovered_value = int(detected_value * 0.6)  # Assume 60% of detected value is recoverable

    final_output = {
        "summary": ai_result.get("summary", text[:120]),
        "reasoning": reasoning,
        "recommendation": recommendation,
        "sentiment": ai_result.get("sentiment", "neutral"),
        "suggested_action": ai_result.get("suggested_action", "review"),
        "detected_value": detected_value,
        "recovered_value": recovered_value,
        "confidence_score": ai_result.get("confidence_score", 0.5),
    }

    if thread_id:
        if len(_CACHE) >= _CACHE_LIMIT:
            _CACHE.clear()
        _CACHE[thread_id] = final_output

    return final_output
