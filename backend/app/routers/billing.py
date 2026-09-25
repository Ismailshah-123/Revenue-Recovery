# ====================== app/routers/billing.py ======================
import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request

from app import crud, models
from app.config import settings
from app.core.security import get_current_user
from app.database import get_db
from app.schemas import PlanOut
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("routers.billing")
router = APIRouter(prefix="/api/billing", tags=["Billing & Subscriptions"])

stripe.api_key = settings.STRIPE_API_KEY


# ---------------- CURRENT PLAN ----------------
@router.get("/plan", response_model=PlanOut)
async def get_plan(current_user: models.User = Depends(get_current_user)):
    subscription = current_user.workspace.subscription
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found for workspace")

    plan_config = settings.PLANS.get(subscription.plan, {})
    return PlanOut(
        plan=subscription.plan,
        is_active=subscription.is_active,
        email_limit=plan_config.get("email_limit", 0),
        ai_limit=plan_config.get("ai_limit", 0),
        cancel_at_period_end=subscription.cancel_at_period_end,
    )


# ---------------- CREATE CHECKOUT ----------------
@router.post("/create-checkout")
async def create_checkout(
    plan: str,
    current_user: models.User = Depends(get_current_user),
):
    if settings.MVP_MODE:
        logger.info("MVP MODE: returning stub checkout URL")
        return {"checkout_url": f"{settings.FRONTEND_URL}/mvp-upgrade", "mode": "mvp_stub"}

    workspace = current_user.workspace
    subscription = workspace.subscription
    if not subscription:
        raise HTTPException(status_code=400, detail="No subscription found for workspace")

    plan_config = settings.PLANS.get(plan)
    if not plan_config or not plan_config.get("price_id"):
        raise HTTPException(status_code=400, detail="Invalid plan configuration")

    try:
        session = stripe.checkout.Session.create(
            customer=subscription.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": plan_config["price_id"], "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.FRONTEND_URL}/success",
            cancel_url=f"{settings.FRONTEND_URL}/cancel",
            client_reference_id=str(workspace.id),
        )
        logger.info("Stripe checkout created | workspace=%s", workspace.id)
        return {"checkout_url": session.url}
    except Exception as exc:
        logger.exception("Stripe checkout failed")
        raise HTTPException(status_code=500, detail="Stripe checkout failed") from exc


# ---------------- STRIPE WEBHOOK ----------------
@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc

    data = event["data"]["object"]
    workspace_id = int(data.get("client_reference_id", 0))
    subscription = await crud.get_subscription_by_workspace(db, workspace_id)

    if not subscription:
        logger.warning("Webhook received for workspace without subscription | workspace=%s", workspace_id)
        return {"status": "ignored"}

    if event["type"] == "checkout.session.completed":
        subscription.is_active = True
    elif event["type"] == "customer.subscription.deleted":
        subscription.is_active = False

    db.add(subscription)
    await db.commit()
    logger.info("Subscription updated via webhook | workspace=%s active=%s", workspace_id, subscription.is_active)
    return {"status": "success"}
