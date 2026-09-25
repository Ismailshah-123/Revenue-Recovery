# ====================== app/database.py ======================
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings

logger = logging.getLogger("database")


def _to_async_url(url: str) -> str:
    """
    Normalize a DATABASE_URL into one SQLAlchemy's async engine can use.

    Accepts plain 'sqlite://' or 'postgresql://' URLs (the form most
    people copy from a hosting provider) as well as URLs that already
    specify an async driver, and returns a URL with the correct async
    driver attached. This avoids a confusing
    'InvalidRequestError: The asyncio extension requires an async driver'
    error the first time someone points this at a real Postgres database.
    """
    if url.startswith("sqlite+aiosqlite://") or url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        # Some providers (e.g. Heroku-style URLs) still use the old scheme name.
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


DATABASE_URL = _to_async_url(settings.DATABASE_URL)
IS_SQLITE = DATABASE_URL.startswith("sqlite+aiosqlite://")

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG and settings.ENVIRONMENT != "production",
    future=True,
    # SQLite + NullPool avoids "database is locked" surprises under the
    # async driver; Postgres keeps SQLAlchemy's normal pooled engine.
    poolclass=NullPool if IS_SQLITE else None,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    """
    FastAPI dependency that yields a database session.
    Commits automatically on success, rolls back on error.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            logger.exception("Database transaction failed")
            raise
        except Exception:
            await session.rollback()
            logger.exception("Unexpected error during database transaction")
            raise
