# ====================== app/routes.py ======================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas, crud
from app.auth import get_current_user
from app.database import get_db
from app.config import settings
from app.deps import check_feature_limit
from app.services.followup_detector import detect_followups
from app.services.ai_service import generate_insights

router = APIRouter(prefix="/emails", tags=["Emails"])

# ---------------- LIST EMAILS ----------------
@router.get("/", response_model=list[schemas.EmailThreadResponse])
async def list_emails(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return await crud.list_emails(db, user.workspace_id, skip, limit)

# ---------------- GET SINGLE EMAIL ----------------
@router.get("/{thread_id}", response_model=schemas.EmailThreadResponse)
async def get_email(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    email = await crud.get_email_by_thread(db, user.workspace_id, thread_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email

# ---------------- CREATE EMAIL ----------------
@router.post("/", response_model=schemas.EmailThreadResponse, status_code=201)
async def create_email(
    payload: schemas.EmailThreadCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    await check_feature_limit(user.workspace_id, "email_limit")
    return await crud.create_email(db, user.workspace_id, payload.dict())

# ---------------- ANALYZE EMAIL ----------------
@router.post("/{thread_id}/analyze", response_model=schemas.EmailThreadResponse)
async def analyze_email(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    email = await crud.get_email_by_thread(db, user.workspace_id, thread_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    await check_feature_limit(user.workspace_id, "ai_limit")

    needs_followup, confidence = detect_followups(email.snippet)
    ai_insight = await generate_insights(email.snippet, thread_id)

    update_data = {
        "needs_followup": needs_followup,
        "detected_value": int(confidence * 3000),
        "ai_insight": ai_insight,
        "status": "analyzed",
    }

    return await crud.update_email(db, email, update_data)
