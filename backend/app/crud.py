# ====================== app/crud.py ======================
from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import models
from app.core.security import hash_password

# ============================================================
# WORKSPACES
# ============================================================

async def create_workspace(db: AsyncSession, name: str) -> models.Workspace:
    if not name or not name.strip():
        raise ValueError("Workspace name cannot be empty")

    ws = models.Workspace(name=name.strip())
    db.add(ws)

    try:
        await db.commit()
        await db.refresh(ws)
        return ws
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError("Workspace with this name already exists") from exc


async def get_workspace(db: AsyncSession, workspace_id: int) -> Optional[models.Workspace]:
    result = await db.execute(select(models.Workspace).where(models.Workspace.id == workspace_id))
    return result.scalars().first()


async def list_workspaces(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Workspace).offset(skip).limit(min(limit, 500)))
    return result.scalars().all()


# ============================================================
# SUBSCRIPTIONS
# ============================================================

async def create_default_subscription(
    db: AsyncSession,
    workspace: models.Workspace,
    plan: str = "starter",
) -> models.Subscription:
    """
    Every workspace needs a subscription row for the billing/feature-limit
    dependencies to work. The original code never created one at signup,
    so get_active_subscription() would 403 for every brand-new workspace
    the moment MVP_MODE was turned off.
    """
    sub = models.Subscription(workspace_id=workspace.id, plan=plan, is_active=True)
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def get_subscription_by_workspace(db: AsyncSession, workspace_id: int) -> Optional[models.Subscription]:
    result = await db.execute(
        select(models.Subscription).where(models.Subscription.workspace_id == workspace_id)
    )
    return result.scalars().first()


# ============================================================
# USERS
# ============================================================

async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    workspace: models.Workspace,
    role: str = "member",
) -> models.User:
    if not workspace or not workspace.id:
        raise ValueError("Invalid workspace")

    user = models.User(
        email=email.lower().strip(),
        hashed_password=hash_password(password),
        workspace_id=workspace.id,
        role=role,
    )
    db.add(user)

    try:
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError("User with this email already exists in this workspace") from exc


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    result = await db.execute(select(models.User).where(models.User.email == email.lower().strip()))
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[models.User]:
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalars().first()


async def list_users(db: AsyncSession, workspace_id: int, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(models.User)
        .where(models.User.workspace_id == workspace_id)
        .offset(skip)
        .limit(min(limit, 500))
    )
    return result.scalars().all()


# ============================================================
# EMAIL THREADS
# ============================================================

async def create_email(db: AsyncSession, workspace_id: int, payload: dict) -> models.EmailThread:
    email = models.EmailThread(workspace_id=workspace_id, **payload)
    db.add(email)

    try:
        await db.commit()
        await db.refresh(email)
        return email
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError("Email thread already exists") from exc


async def get_email_by_thread(db: AsyncSession, workspace_id: int, thread_id: str):
    result = await db.execute(
        select(models.EmailThread)
        .where(models.EmailThread.workspace_id == workspace_id)
        .where(models.EmailThread.thread_id == thread_id)
    )
    return result.scalars().first()


async def update_email(db: AsyncSession, email_obj: models.EmailThread, updates: dict) -> models.EmailThread:
    for key, value in updates.items():
        setattr(email_obj, key, value)

    email_obj.updated_at = datetime.utcnow()
    db.add(email_obj)
    await db.commit()
    await db.refresh(email_obj)
    return email_obj


async def list_emails(db: AsyncSession, workspace_id: int, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(models.EmailThread)
        .where(models.EmailThread.workspace_id == workspace_id)
        .order_by(models.EmailThread.created_at.desc())
        .offset(skip)
        .limit(min(limit, 500))
    )
    return result.scalars().all()


# ============================================================
# FEATURE USAGE TRACKING (plan-limit enforcement & analytics)
# ============================================================

async def record_feature_usage(
    db: AsyncSession,
    workspace_id: int,
    feature: str,
    quantity: int = 1,
) -> models.FeatureUsage:
    result = await db.execute(
        select(models.FeatureUsage)
        .where(models.FeatureUsage.workspace_id == workspace_id)
        .where(models.FeatureUsage.feature == feature)
    )
    usage_obj = result.scalars().first()

    if usage_obj:
        usage_obj.quantity += quantity
    else:
        usage_obj = models.FeatureUsage(workspace_id=workspace_id, feature=feature, quantity=quantity)

    db.add(usage_obj)
    await db.commit()
    await db.refresh(usage_obj)
    return usage_obj


async def get_feature_usage(db: AsyncSession, workspace_id: int, feature: str) -> int:
    result = await db.execute(
        select(models.FeatureUsage)
        .where(models.FeatureUsage.workspace_id == workspace_id)
        .where(models.FeatureUsage.feature == feature)
    )
    usage_obj = result.scalars().first()
    return usage_obj.quantity if usage_obj else 0
