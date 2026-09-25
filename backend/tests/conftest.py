# ====================== tests/conftest.py ======================
"""
Test environment must be configured *before* app.config is first
imported (Settings() is built once, at import time), so the env vars
below are set at module load, ahead of any `from app...` import.

Uses a temp-file-backed SQLite database rather than ':memory:' --
SQLAlchemy's async sqlite driver opens a fresh connection per checkout,
and a ':memory:' database is private to a single connection, so tables
created on one connection would be invisible on the next. A temp file
avoids that entirely and needs no pooling workarounds.
"""
import os
import tempfile
from pathlib import Path

_TEST_DB_PATH = Path(tempfile.mkdtemp()) / "test.db"

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-not-used-in-production-32chars")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB_PATH}")
os.environ.setdefault("MVP_MODE", "true")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("AI_API_KEY", "")
os.environ.setdefault("GMAIL_CLIENT_ID", "")
os.environ.setdefault("GMAIL_CLIENT_SECRET", "")
os.environ.setdefault("GMAIL_REFRESH_TOKEN", "")
os.environ.setdefault("GMAIL_USER", "")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _fresh_schema():
    """Drops and recreates every table before each test, for full isolation."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient):
    """An AsyncClient pre-authenticated as a freshly signed-up user."""
    signup_payload = {
        "email": "founder@example.com",
        "password": "correct-horse-battery-staple",
        "company": "Acme Revenue Co",
    }
    resp = await client.post("/api/auth/signup", json=signup_payload)
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
