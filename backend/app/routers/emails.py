# ====================== app/routers/emails.py ======================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.core.security import get_current_user
from app.database import get_db
from app.deps import check_feature_limit
from app.services.ai_service import generate_insights
from app.services.followup_detector import detect_followups

router = APIRouter(prefix="/emails", tags=["Emails"])


@router.get("/", response_model=list[schemas.EmailThreadResponse])
async def list_emails(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return await crud.list_emails(db, user.workspace_id, skip, limit)


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


@router.post("/", response_model=schemas.EmailThreadResponse, status_code=201)
async def create_email(
    payload: schemas.EmailThreadCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    await check_feature_limit(db, user.workspace_id, "email_limit")
    return await crud.create_email(db, user.workspace_id, payload.model_dump())


@router.post("/{thread_id}/analyze", response_model=schemas.EmailThreadResponse)
async def analyze_email(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    email = await crud.get_email_by_thread(db, user.workspace_id, thread_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    await check_feature_limit(db, user.workspace_id, "ai_limit")

    needs_followup, confidence = detect_followups(email.snippet)
    ai_result = await generate_insights(email.snippet, thread_id)

    update_data = {
        "needs_followup": needs_followup,
        "detected_value": max(int(confidence * 3000), ai_result["detected_value"]),
        "recovered_value": ai_result["recovered_value"],
        "ai_insight": ai_result["reasoning"],
        "status": "analyzed",
    }

    return await crud.update_email(db, email, update_data)
