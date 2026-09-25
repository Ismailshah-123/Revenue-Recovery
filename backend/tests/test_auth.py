# ====================== tests/test_auth.py ======================
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_signup_returns_token_pair(client: AsyncClient):
    resp = await client.post(
        "/api/auth/signup",
        json={"email": "a@example.com", "password": "supersecret1", "company": "Acme"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_signup_duplicate_email_rejected(client: AsyncClient):
    payload = {"email": "dupe@example.com", "password": "supersecret1", "company": "Acme"}
    first = await client.post("/api/auth/signup", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/auth/signup", json=payload)
    assert second.status_code == 400


async def test_signup_requires_company_name(client: AsyncClient):
    resp = await client.post(
        "/api/auth/signup",
        json={"email": "nocompany@example.com", "password": "supersecret1"},
    )
    assert resp.status_code == 422


async def test_login_with_correct_credentials(client: AsyncClient):
    await client.post(
        "/api/auth/signup",
        json={"email": "login@example.com", "password": "supersecret1", "company": "Acme"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "supersecret1"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_login_with_wrong_password_rejected(client: AsyncClient):
    await client.post(
        "/api/auth/signup",
        json={"email": "wrongpass@example.com", "password": "supersecret1", "company": "Acme"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "wrongpass@example.com", "password": "not-the-password"},
    )
    assert resp.status_code == 401


async def test_me_returns_workspace_and_plan(auth_client: AsyncClient):
    resp = await auth_client.get("/api/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "founder@example.com"
    assert body["workspace_name"] == "Acme Revenue Co"
    assert body["plan"] == "starter"
    # The user who signs up and creates the workspace is its admin
    # (needed to see the billing/Settings page).
    assert body["role"] == "admin"


async def test_me_without_token_rejected(client: AsyncClient):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_refresh_issues_new_access_token(client: AsyncClient):
    signup = await client.post(
        "/api/auth/signup",
        json={"email": "refresh@example.com", "password": "supersecret1", "company": "Acme"},
    )
    refresh_token = signup.json()["refresh_token"]

    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_refresh_rejects_access_token(client: AsyncClient):
    """An access token used where a refresh token belongs must be rejected."""
    signup = await client.post(
        "/api/auth/signup",
        json={"email": "wrongtokentype@example.com", "password": "supersecret1", "company": "Acme"},
    )
    access_token = signup.json()["access_token"]

    resp = await client.post("/api/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
