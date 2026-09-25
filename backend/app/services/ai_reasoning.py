# ====================== app/services/ai_reasoning.py ======================
"""
AI REASONING SERVICE
---------------------
- Revenue-focused insights from an email snippet
- Deterministic, validated JSON output
- Safe fallback if the AI call fails or the API key isn't configured
"""
import json
import logging
from typing import Literal, Optional, TypedDict

from openai import OpenAI

from app.config import settings

logger = logging.getLogger("ai_reasoning")

MODEL_NAME = "gpt-4o-mini"
MAX_INPUT_CHARS = 2000
TIMEOUT_SECONDS = 15
BASE_DEAL_VALUE = 3000  # Default estimated revenue per opportunity

# The original code read os.getenv("OPENAI_API_KEY") directly, but the
# .env file (and Settings) define this as AI_API_KEY -- so the lookup
# always returned None and the whole backend refused to start. Reading it
# from `settings` also means test suites can run with AI_API_KEY unset
# and just exercise the fallback path below, instead of crashing on import.
_client: Optional[OpenAI] = OpenAI(api_key=settings.AI_API_KEY) if settings.AI_API_KEY else None

Sentiment = Literal["positive", "neutral", "negative"]
Urgency = Literal["low", "medium", "high"]
RevenueSignal = Literal["none", "possible", "likely"]


class EmailInsights(TypedDict):
    summary: str
    sentiment: Sentiment
    urgency: Urgency
    revenue_signal: RevenueSignal
    detected_value: int
    reasoning: str
    suggested_action: str
    confidence_score: float


def _safe_fallback(snippet: str) -> EmailInsights:
    """Returned when the AI call fails, or no API key is configured."""
    return {
        "summary": snippet[:120] or "Customer message received.",
        "sentiment": "neutral",
        "urgency": "medium",
        "revenue_signal": "possible",
        "detected_value": BASE_DEAL_VALUE,
        "reasoning": (
            "Message could not be analyzed. "
            "Similar messages often require follow-up to recover potential revenue."
        ),
        "suggested_action": "Review and consider sending a follow-up.",
        "confidence_score": 0.5,
    }


def _validate_payload(data: dict, snippet: str) -> EmailInsights:
    """Ensures AI output is deterministic and safe even if the model misbehaves."""
    try:
        confidence = float(data.get("confidence_score", 0.5))
    except (ValueError, TypeError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))

    detected_value = int(BASE_DEAL_VALUE * confidence)

    sentiment = data.get("sentiment", "neutral")
    if sentiment not in ("positive", "neutral", "negative"):
        sentiment = "neutral"

    urgency = data.get("urgency", "medium")
    if urgency not in ("low", "medium", "high"):
        urgency = "medium"

    revenue_signal = data.get("revenue_signal", "possible")
    if revenue_signal not in ("none", "possible", "likely"):
        revenue_signal = "possible"

    return {
        "summary": data.get("summary", snippet[:120]),
        "sentiment": sentiment,
        "urgency": urgency,
        "revenue_signal": revenue_signal,
        "detected_value": detected_value,
        "reasoning": data.get("reasoning", "This message may represent a missed revenue opportunity."),
        "suggested_action": data.get(
            "suggested_action", "Consider sending a follow-up to recover potential revenue."
        ),
        "confidence_score": confidence,
    }


def analyze_email_with_ai(snippet: str) -> EmailInsights:
    """
    Analyze an email snippet using AI. Always returns a valid EmailInsights
    dict -- falls back to a safe default if no API key is set or the call
    fails for any reason, so a flaky or unconfigured AI provider never
    takes down the request.
    """
    if not snippet.strip():
        return _safe_fallback("")

    snippet = snippet[:MAX_INPUT_CHARS]

    if _client is None:
        logger.warning("AI_API_KEY is not configured; returning fallback insight")
        return _safe_fallback(snippet)

    prompt = f"""You are a revenue recovery assistant for sales teams.
Your task is to:
1. Detect missed opportunities
2. Estimate potential revenue loss
3. Suggest actionable steps
4. Provide human-readable reasoning

Respond ONLY in valid JSON with the following keys:
- summary (string)
- sentiment (positive | neutral | negative)
- urgency (low | medium | high)
- revenue_signal (none | possible | likely)
- reasoning (string)
- suggested_action (string)
- confidence_score (float 0-1)

EMAIL:
'''{snippet}'''
"""

    try:
        response = _client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=350,
            timeout=TIMEOUT_SECONDS,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
        data = json.loads(raw_content)
        return _validate_payload(data, snippet)
    except Exception:
        logger.exception("AI reasoning failed")
        return _safe_fallback(snippet)
