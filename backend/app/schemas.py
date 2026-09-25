# ====================== app/schemas.py ======================
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

# ============================================================
# AUTH SCHEMAS
# ============================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    company: str = Field(..., min_length=2, max_length=128, description="Company / Workspace name")


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    workspace_id: int
    workspace_name: str
    plan: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ============================================================
# EMAIL THREAD SCHEMAS
# ============================================================

Sentiment = Literal["positive", "neutral", "negative"]
Urgency = Literal["low", "medium", "high"]
RevenueSignal = Literal["none", "possible", "likely"]


class AIInsight(BaseModel):
    summary: str
    sentiment: Sentiment
    urgency: Urgency
    revenue_signal: RevenueSignal
    detected_value: int
    reasoning: str
    suggested_action: str
    confidence_score: float


class EmailThreadCreate(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=255)
    subject: Optional[str] = Field(None, max_length=255)
    sender: Optional[str] = Field(None, max_length=255)
    snippet: str = Field(..., min_length=1)
    needs_followup: bool = False
    # Stored as free text (a human-readable reasoning string), not the
    # full structured AIInsight object -- see services/ai_service.py.
    ai_insight: Optional[str] = None
    detected_value: int = 0
    status: str = "new"


class EmailThreadResponse(BaseModel):
    id: int
    workspace_id: int
    thread_id: str
    subject: Optional[str]
    sender: Optional[str]
    snippet: str
    needs_followup: bool
    ai_insight: Optional[str] = None
    status: str
    detected_value: int = Field(0, description="Estimated money value in USD")
    recovered_value: int = Field(0, description="Estimated recovered value in USD")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmailThreadStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=50, description="New status of the email thread")


# ============================================================
# BILLING SCHEMAS
# ============================================================

class PlanOut(BaseModel):
    plan: str
    is_active: bool
    email_limit: int
    ai_limit: int
    cancel_at_period_end: bool = False
