# ====================== app/core/security.py ======================
"""
Single source of truth for password hashing and JWT handling.

The original codebase had this logic duplicated, inconsistently, across
five different files (app/auth.py, app/security.py, app/utils/security.py,
app/services/auth.py, app/services/auth_dependencies.py) with three
different create_access_token() signatures. Only app/auth.py's version was
actually imported anywhere; the other four were dead code, and the one
call site that mattered (signup/login) was calling the dict-based
signature from a module it never imported, which raised a TypeError on
every signup and login attempt. This module replaces all five.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.database import get_db
from app.models import User

logger = logging.getLogger("security")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ------------------------------------------------------------
# PASSWORDS
# ------------------------------------------------------------
def hash_password(password: str) -> str:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# ------------------------------------------------------------
# JWT CREATION
# ------------------------------------------------------------
def _build_token(user_id: int, workspace_id: int, token_type: str, expire: datetime) -> str:
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "workspace_id": workspace_id,
        "iat": datetime.utcnow(),
        "exp": expire,
        "iss": settings.APP_NAME,
        "aud": "frontend",
        "type": token_type,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    user_id: int,
    workspace_id: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    token = _build_token(user_id, workspace_id, "access", expire)
    logger.info("Access token issued | user=%s workspace=%s", user_id, workspace_id)
    return token


def create_refresh_token(
    user_id: int,
    workspace_id: int,
    expires_days: Optional[int] = None,
) -> str:
    expire = datetime.utcnow() + timedelta(days=expires_days or settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token = _build_token(user_id, workspace_id, "refresh", expire)
    logger.info("Refresh token issued | user=%s workspace=%s", user_id, workspace_id)
    return token


def create_token_pair(user_id: int, workspace_id: int) -> Dict[str, str]:
    return {
        "access_token": create_access_token(user_id, workspace_id),
        "refresh_token": create_refresh_token(user_id, workspace_id),
    }


# ------------------------------------------------------------
# JWT DECODING
# ------------------------------------------------------------
def decode_token(token: str, expected_type: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT, raising HTTPException(401) on any problem:
    bad signature, expired, wrong audience/issuer, or wrong token type
    (e.g. someone passing a refresh token where an access token belongs).
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience="frontend",
            issuer=settings.APP_NAME,
        )
        if payload.get("type") != expected_type:
            raise JWTError(f"Expected a {expected_type} token")
        return payload
    except JWTError as exc:
        logger.warning("Token rejected: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ------------------------------------------------------------
# CURRENT USER DEPENDENCY
# ------------------------------------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token, expected_type="access")

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc
    workspace_id = payload.get("workspace_id")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalars().first()

    if not user or user.workspace_id != workspace_id:
        logger.warning("Unauthorized access attempt | user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

    return user


def require_role(*roles: str):
    """
    Factory for a role-gated dependency, e.g.:
        Depends(require_role("admin"))
    """
    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _checker
