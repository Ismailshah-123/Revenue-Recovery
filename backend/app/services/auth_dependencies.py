# ====================== app/services/auth_dependencies.py ======================
"""
AUTH DEPENDENCIES (ENTERPRISE-PREMIUM)
--------------------------------------
Centralized user authentication for FastAPI
- JWT verification
- Token type validation
- Workspace isolation
- Structured exceptions
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
import logging

from app.database import get_db
from app import models
from app.config import settings

logger = logging.getLogger("auth_dependencies")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> models.User:
    """
    Get current authenticated user.
    Raises 401 if token invalid or user inactive.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("type") != "access":
            raise ValueError("Invalid token type")

        user_id = payload.get("user_id")
        workspace_id = payload.get("workspace_id")

        if not user_id or not workspace_id:
            raise ValueError("Token missing essential claims")

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please login again.",
        )
    except Exception as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    result = await db.execute(
        models.User.__table__.select()
        .where(models.User.id == user_id)
        .where(models.User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or user.workspace_id != workspace_id:
        logger.warning(f"Unauthorized access attempt | user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access",
        )

    logger.debug(f"[AUTH] User validated | user_id={user.id} workspace_id={user.workspace_id}")
    return user
