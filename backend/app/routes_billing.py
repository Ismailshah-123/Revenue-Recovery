# ====================== app/routes_billing.py ======================
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import stripe
import logging

from app.auth import get_current_user
from app import models, crud
from app.config import settings
from app.database import get_db

logger = logging.getLogger("billing")
router = APIRouter(prefix="/api/billing", tags=["Billing & Subscriptions"])

# ---------------- MVP MODE ----------------
if settings.MVP_MODE:

    @router.post("/create-checkout")
    async def create_checkout_mvp():
        logger.warning("MVP MODE: Returning stub checkout URL")
        return {"checkout_url": f"{settings.FRONTEND_URL}/mvp-upgrade", "mode": "mvp_stub"}

# ---------------- STRIPE CONFIG ----------------
stripe.api_key = settings.STRIPE_API_KEY

# ---------------- CREATE CHECKOUT ----------------
@router.post("/create-checkout")
async def create_checkout(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if settings.MVP_MODE:
        raise HTTPException(status_code=400, detail="Stripe disabled in MVP mode")

    workspace = current_user.workspace
    subscription = workspace.subscription

    if not subscription:
        raise HTTPException(status_code=400, detail="No subscription found for workspace")

    plan_config = settings.PLANS.get(subscription.plan)
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
        logger.info(f"Stripe checkout created | workspace={workspace.id}")
        return {"checkout_url": session.url}

    except Exception as e:
        logger.exception("Stripe checkout failed")
        raise HTTPException(status_code=500, detail="Stripe checkout failed")

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
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    data = event["data"]["object"]
    workspace_id = int(data.get("client_reference_id", 0))
    subscription = await crud.get_subscription_by_workspace(db, workspace_id)

    if not subscription:
        logger.warning(f"Webhook received for workspace without subscription | workspace={workspace_id}")
        return {"status": "ignored"}

    # Handle subscription events
    if event["type"] == "checkout.session.completed":
        subscription.is_active = True
    elif event["type"] == "customer.subscription.deleted":
        subscription.is_active = False

    db.add(subscription)
    await db.commit()
    logger.info(f"Subscription updated via webhook | workspace={workspace_id} | active={subscription.is_active}")
    return {"status": "success"}
