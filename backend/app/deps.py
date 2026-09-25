# ====================== app/deps.py ======================
"""
FastAPI dependencies and plan-limit enforcement.

The original check_feature_limit() was declared with Depends(...) default
arguments (the pattern FastAPI expects for a value that gets *added to a
route's signature*), but every call site invoked it directly, as a plain
awaited function, from inside another route's body. That meant `workspace`,
`subscription` and `db` never received real objects -- they'd be literal
fastapi.params.Depends instances, and the function would crash the first
time MVP_MODE was turned off. This version matches how it's actually used:
a plain async helper called with concrete arguments.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.config import settings
from app.core.security import get_current_user
from app.database import get_db
from app.models import User, Workspace


async def get_current_workspace(
    user: User = Depends(get_current_user),
) -> Workspace:
    """Returns the current user's active workspace. Enforces multi-tenant isolation."""
    workspace = user.workspace
    if not workspace or not workspace.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace not found or inactive")
    return workspace


async def check_feature_limit(
    db: AsyncSession,
    workspace_id: int,
    feature: str,
    increment: int = 1,
) -> bool:
    """
    Checks a feature's usage against the workspace's plan limit and records
    the usage. In MVP_MODE (the default), this is a no-op that always
    passes -- billing/limits are not enforced until MVP_MODE is turned off.
    """
    if settings.MVP_MODE:
        return True

    subscription = await crud.get_subscription_by_workspace(db, workspace_id)
    if not subscription or not subscription.is_active:
        raise HTTPException(status_code=403, detail="No active subscription found for this workspace")

    plan_config = settings.PLANS.get(subscription.plan, {})
    limit = plan_config.get(feature, float("inf"))

    current_usage = await crud.get_feature_usage(db, workspace_id, feature)
    if current_usage + increment > limit:
        raise HTTPException(
            status_code=403,
            detail=f"Plan limit reached for '{feature}' ({current_usage}/{limit})",
        )

    await crud.record_feature_usage(db, workspace_id, feature, quantity=increment)
    return True
