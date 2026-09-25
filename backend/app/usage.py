# ====================== app/usage.py ======================
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app import models

async def record_feature_usage(
    db: AsyncSession,
    workspace_id: int,
    feature: str,
    quantity: int = 1,
):
    usage = models.FeatureUsage(
        workspace_id=workspace_id,
        feature=feature,
        quantity=quantity,
        used_at=datetime.utcnow(),
    )
    db.add(usage)
    await db.commit()
