# ====================== app/routers/auth.py ======================
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.core.security import (
    create_token_pair,
    decode_token,
    get_current_user,
    verify_password,
)
from app.database import get_db

logger = logging.getLogger("routers.auth")
router = APIRouter(prefix="/api/auth", tags=["Auth"])


# ---------------- REQUEST SCHEMAS ----------------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    company: Optional[str] = None
    workspace_name: Optional[str] = None

    def get_company_name(self) -> str:
        return self.company or self.workspace_name or ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _user_out(user: models.User) -> schemas.UserOut:
    plan = user.workspace.subscription.plan if user.workspace.subscription else "starter"
    return schemas.UserOut(
        id=user.id,
        email=user.email,
        role=user.role,
        workspace_id=user.workspace_id,
        workspace_name=user.workspace.name,
        plan=plan,
        created_at=user.created_at,
    )


# ---------------- SIGNUP ----------------
@router.post("/signup", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    company_name = payload.get_company_name()
    if not company_name:
        raise HTTPException(status_code=422, detail="Company or workspace name is required")

    existing_user = await crud.get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    workspace = await crud.create_workspace(db, name=company_name)
    await crud.create_default_subscription(db, workspace)
    # The signup flow only ever creates one user per new workspace, and
    # that person is the one who needs to manage billing -- so they
    # become "admin", not the "member" default. Without this, nobody
    # could ever see the Settings/billing page after signing up, since
    # nothing else in the app ever promotes a user to admin.
    user = await crud.create_user(db, email=payload.email, password=payload.password, workspace=workspace, role="admin")

    tokens = create_token_pair(user.id, workspace.id)
    return schemas.TokenResponse(**tokens)


# ---------------- LOGIN ----------------
@router.post("/login", response_model=schemas.TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email(db, payload.email)
    if not user or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    tokens = create_token_pair(user.id, user.workspace_id)
    return schemas.TokenResponse(**tokens)


# ---------------- REFRESH ----------------
@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh(payload: schemas.RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_payload = decode_token(payload.refresh_token, expected_type="refresh")
    user = await crud.get_user_by_id(db, int(token_payload["sub"]))

    if not user or not user.is_active or user.workspace_id != token_payload.get("workspace_id"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    tokens = create_token_pair(user.id, user.workspace_id)
    return schemas.TokenResponse(**tokens)


# ---------------- CURRENT USER ----------------
@router.get("/me", response_model=schemas.UserOut)
async def get_me(user: models.User = Depends(get_current_user)):
    return _user_out(user)
