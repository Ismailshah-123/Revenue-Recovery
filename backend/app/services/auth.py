# ====================== app/services/auth.py ======================
"""
AUTH SERVICE (ENTERPRISE-PREMIUM)
---------------------------------
Secure authentication for SaaS MVP:
- JWT access tokens
- Optional refresh tokens
- Bcrypt password hashing
- Human-readable logs
"""

from datetime import datetime, timedelta
from typing import Optional
import logging
import jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger("auth")

# ---------------- PASSWORD CONTEXT ----------------
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    """Hashes plain password"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verifies password"""
    return pwd_context.verify(plain, hashed)

# ---------------- JWT TOKENS ----------------
def create_access_token(
    *,
    user_id: int,
    workspace_id: int,
    expires_minutes: Optional[int] = None,
) -> str:
    """Generate JWT access token"""
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "user_id": user_id,
        "workspace_id": workspace_id,
        "type": "access",
        "iat": datetime.utcnow(),
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    logger.info(f"[AUTH] Access token issued | user={user_id} workspace={workspace_id}")
    return token

def create_refresh_token(
    *,
    user_id: int,
    workspace_id: int,
    expires_days: int = 30
) -> str:
    """Optional refresh token"""
    expire = datetime.utcnow() + timedelta(days=expires_days)
    payload = {
        "user_id": user_id,
        "workspace_id": workspace_id,
        "type": "refresh",
        "iat": datetime.utcnow(),
        "exp": expire,
    }
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    logger.info(f"[AUTH] Refresh token issued | user={user_id} workspace={workspace_id}")
    return token
