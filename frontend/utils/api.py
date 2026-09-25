# ====================== utils/api.py ======================
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_fixed
import requests

BACKEND_URL = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")
TIMEOUT = 10


# ===================== CORE REQUEST ENGINE =====================
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def _request(method, path, token=None, silent=False, **kwargs):
    headers = kwargs.pop("headers", {})
    headers["Content-Type"] = "application/json"

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            method=method,
            url=f"{BACKEND_URL}{path}",
            headers=headers,
            timeout=TIMEOUT,
            **kwargs,
        )

        if response.status_code == 204:
            return {}

        response.raise_for_status()
        return response.json()

    except requests.HTTPError as e:
        status = e.response.status_code

        if status == 401:
            if not silent:
                st.error("Your session has expired. Please login again.")
            st.session_state.pop("token", None)
            st.session_state.pop("user", None)
            st.rerun()

        if not silent:
            st.error(f"Server error ({status}). Please retry.")

        return None

    except requests.RequestException:
        if not silent:
            st.error("Cannot reach backend. Check that the API server is running.")
        return None


# ===================== USER =====================
def get_current_user(token):
    return _request("GET", "/api/auth/me", token=token)


def safe_get_current_user():
    """Fetch the current user, using the session cache when available.
    Clears an invalid/expired session and stops the script rather than
    letting the rest of the page render with no user."""
    user = st.session_state.get("user")
    token = st.session_state.get("token")

    if user and token:
        return user

    if token:
        user = get_current_user(token)
        if user:
            st.session_state["user"] = user
            return user

        st.session_state.pop("token", None)
        st.session_state.pop("user", None)
        st.warning("Session expired. Please login again.")
        st.stop()

    return None


# ===================== EMAILS =====================
def get_emails(token, limit=50):
    return _request(
        "GET",
        "/emails/",
        token=token,
        params={"limit": limit},
        silent=True,
    ) or []


def create_email(token, thread_id, subject, sender, snippet, needs_followup=False):
    return _request(
        "POST",
        "/emails/",
        token=token,
        json={
            "thread_id": thread_id,
            "subject": subject,
            "sender": sender,
            "snippet": snippet,
            "needs_followup": needs_followup,
        },
    )


def analyze_thread(token, thread_id):
    with st.spinner("AI is analyzing this conversation..."):
        return _request(
            "POST",
            f"/emails/{thread_id}/analyze",
            token=token,
        )


# ===================== BILLING =====================
def get_user_plan(token):
    data = _request("GET", "/api/billing/plan", token=token, silent=True)
    return data.get("plan", "starter") if data else "starter"


def create_checkout_session(token, plan):
    data = _request(
        "POST",
        "/api/billing/create-checkout",
        token=token,
        params={"plan": plan},
    )
    return data.get("checkout_url") if data else None
