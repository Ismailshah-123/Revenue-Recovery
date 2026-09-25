# ====================== app/auth.py ======================
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import User, Workspace
from app.config import settings
from app.usage import record_feature_usage


logger = logging.getLogger("auth")

# ------------------------------------------------------------
# SECURITY CONTEXT
# ------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ------------------------------------------------------------
# PASSWORD UTILITIES
# ------------------------------------------------------------
def hash_password(password: str) -> str:
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long",
        )
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# ------------------------------------------------------------
# JWT UTILITIES
# ------------------------------------------------------------
def create_access_token(
    user_id: int,
    workspace_id: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "workspace_id": workspace_id,
        "iat": datetime.utcnow(),
        "exp": expire,
        "iss": settings.APP_NAME,
        "aud": "frontend",
        "type": "access",
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.info(f"[AUTH] Access token issued for user={user_id}, workspace={workspace_id}")
    return token


def create_refresh_token(
    user_id: int,
    workspace_id: int,
    expires_days: int = 30
) -> str:
    expire = datetime.utcnow() + timedelta(days=expires_days)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "workspace_id": workspace_id,
        "iat": datetime.utcnow(),
        "exp": expire,
        "iss": settings.APP_NAME,
        "aud": "frontend",
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.info(f"[AUTH] Refresh token issued for user={user_id}, workspace={workspace_id}")
    return token

# ------------------------------------------------------------
# CURRENT USER DEPENDENCY
# ------------------------------------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    require_roles: Optional[list[str]] = None,
) -> User:
    """
    Validate JWT access token, return active user, enforce role checks.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience="frontend",
        )

        if payload.get("type") != "access":
            raise JWTError()

        user_id = int(payload.get("sub"))
        workspace_id = payload.get("workspace_id")

    except Exception:
        logger.warning(f"[AUTH] Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
        )
    )
    user = result.scalars().first()

    if not user or user.workspace_id != workspace_id:
        logger.warning(f"[AUTH] Unauthorized access attempt user={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access",
        )

    # --------------------------------------------------------
    # ROLE CHECK
    # --------------------------------------------------------
    if require_roles and user.role not in require_roles:
        logger.warning(f"[AUTH] Forbidden role access user={user_id} role={user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    # --------------------------------------------------------
    # USAGE TRACKING
    # --------------------------------------------------------
    try:
        await record_feature_usage(db, user.workspace_id, feature="login")
    except Exception:
        logger.exception(f"[AUTH] Failed to record feature usage for user={user_id}")

    return user
