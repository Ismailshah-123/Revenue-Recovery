# ====================== app/config.py ======================
from typing import Dict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application configuration.
    All values are loaded from environment variables / .env file.
    Required fields (no default) will raise a clear validation error
    on startup if missing, instead of failing later with a confusing
    AttributeError somewhere deep in the code.
    """

    # ---------------- APP ----------------
    APP_NAME: str = "AI Revenue Recovery SaaS"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|production)$")
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:8501"

    # ---------------- SECURITY ----------------
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ---------------- DATABASE ----------------
    DATABASE_URL: str

    # ---------------- GMAIL ----------------
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REFRESH_TOKEN: str = ""
    GMAIL_USER: str = ""

    # ---------------- AI ----------------
    AI_API_KEY: str = ""
    MVP_MODE: bool = True

    # ---------------- FEATURE LIMITS ----------------
    MAX_EMAIL_THREADS: int = 20
    MAX_AI_CALLS: int = 50

    # ---------------- BILLING / STRIPE ----------------
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ---------------- PLANS ----------------
    PLANS: Dict[str, Dict[str, int | str]] = {
        "starter": {"email_limit": 100, "ai_limit": 50, "price_id": ""},
        "growth": {"email_limit": 500, "ai_limit": 250, "price_id": ""},
        "pro": {"email_limit": 5000, "ai_limit": 2000, "price_id": ""},
    }

    # ---------------- ANALYTICS ----------------
    ENABLE_ANALYTICS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
