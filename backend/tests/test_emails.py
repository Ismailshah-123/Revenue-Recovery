# ====================== tests/test_emails.py ======================
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_email(client: AsyncClient, thread_id="thread-1", snippet="Any update on this? Please respond asap."):
    return await client.post(
        "/emails/",
        json={
            "thread_id": thread_id,
            "subject": "Re: Invoice #123",
            "sender": "customer@client.com",
            "snippet": snippet,
        },
    )


async def test_create_and_list_emails(auth_client: AsyncClient):
    create_resp = await _create_email(auth_client)
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    assert body["thread_id"] == "thread-1"
    assert body["status"] == "new"

    list_resp = await auth_client.get("/emails/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


async def test_get_single_email(auth_client: AsyncClient):
    await _create_email(auth_client, thread_id="thread-42")
    resp = await auth_client.get("/emails/thread-42")
    assert resp.status_code == 200
    assert resp.json()["thread_id"] == "thread-42"


async def test_get_missing_email_returns_404(auth_client: AsyncClient):
    resp = await auth_client.get("/emails/does-not-exist")
    assert resp.status_code == 404


async def test_analyze_email_persists_ai_insight_and_recovered_value(auth_client: AsyncClient):
    await _create_email(
        auth_client,
        thread_id="thread-analyze",
        snippet="This is urgent, please respond asap, we need next steps.",
    )

    resp = await auth_client.post("/emails/thread-analyze/analyze")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["status"] == "analyzed"
    assert body["needs_followup"] is True
    assert body["ai_insight"]  # populated by the AI fallback path (no AI_API_KEY in tests)
    assert body["detected_value"] > 0
    assert body["recovered_value"] > 0  # was silently discarded before the fix


async def test_analyze_missing_email_returns_404(auth_client: AsyncClient):
    resp = await auth_client.post("/emails/does-not-exist/analyze")
    assert resp.status_code == 404


async def test_emails_are_isolated_per_workspace(client: AsyncClient):
    # Workspace A creates an email.
    a_signup = await client.post(
        "/api/auth/signup",
        json={"email": "a@workspace-a.com", "password": "supersecret1", "company": "Workspace A"},
    )
    token_a = a_signup.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token_a}"
    await _create_email(client, thread_id="shared-thread-id")

    # Workspace B must not see workspace A's email, even with the same thread_id.
    b_signup = await client.post(
        "/api/auth/signup",
        json={"email": "b@workspace-b.com", "password": "supersecret1", "company": "Workspace B"},
    )
    token_b = b_signup.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token_b}"

    list_resp = await client.get("/emails/")
    assert list_resp.json() == []

    get_resp = await client.get("/emails/shared-thread-id")
    assert get_resp.status_code == 404
