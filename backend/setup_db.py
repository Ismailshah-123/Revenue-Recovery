# setup_db.py
"""
One-off manual database initialization script.

Usage:
    python setup_db.py

Note: app/main.py's lifespan already runs this same create_all() step
automatically every time the API server starts, so you generally don't
need to run this by hand -- it's here for scripting/CI use, or for
inspecting the schema without booting the full API.

The original version called the *synchronous* Base.metadata.create_all(
bind=engine), but app/database.py's `engine` is an async engine
(create_async_engine) -- passing it to the sync create_all() raises
immediately. This version uses the async pattern instead.
"""
import asyncio

from app.database import Base, engine
from app import models  # noqa: F401  (import ensures models are registered on Base.metadata)


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized")


if __name__ == "__main__":
    asyncio.run(main())
