# ====================== app/routes_auth.py ======================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from app.database import get_db
from app import models, crud, schemas
from app.auth import hash_password, verify_password, create_access_token, get_current_user

logger = logging.getLogger("routes_auth")
router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ---------------- REQUEST SCHEMAS ----------------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    company: Optional[str] = None
    workspace_name: Optional[str] = None

    def get_company_name(self) -> str:
        return self.company or self.workspace_name

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ---------------- SIGNUP ----------------
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    company_name = payload.get_company_name()
    if not company_name:
        raise HTTPException(status_code=422, detail="Company or workspace name is required")

    existing_user = await crud.get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    workspace = await crud.create_workspace(db, name=company_name)
    user = await crud.create_user(db, email=payload.email, password=payload.password, workspace=workspace)

    token = create_access_token({
        "sub": str(user.id),
        "workspace_id": workspace.id
    })

    return {"access_token": token, "token_type": "bearer"}

# ---------------- LOGIN ----------------
@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email(db, payload.email)
    if not user or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": str(user.id),
        "workspace_id": user.workspace_id
    })

    return {"access_token": token, "token_type": "bearer"}

# ---------------- CURRENT USER ----------------
@router.get("/me", response_model=schemas.UserOut)
async def get_me(user: models.User = Depends(get_current_user)):
    return user
