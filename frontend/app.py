# ====================== app.py ======================
import datetime
import time

import streamlit as st

from utils.auth import login, logout, signup
from utils.api import get_emails, safe_get_current_user
from utils.helpers import format_snippet

from views.dashboard import render_dashboard
from views.analytics import render_analytics
from views.recovery_pipeline import render_recovery_pipeline
from views.settings import render_settings

st.set_page_config(page_title="Revenue Recovery AI", page_icon="💸", layout="wide")

TIMEOUT = 10

# ===================== SESSION DEFAULTS =====================
SESSION_DEFAULTS = {
    "token": None,
    "refresh_token": None,
    "user": None,
    "last_refresh": time.time(),
}
for k, v in SESSION_DEFAULTS.items():
    st.session_state.setdefault(k, v)

# ===================== GLOBAL PREMIUM STYLES =====================
st.markdown("""
<style>
html, body, [class*="css"] { font-family: Inter, system-ui, sans-serif; }
.main { background: #f6f8fb; }
.topbar { display:flex; justify-content:space-between; align-items:center; padding:14px 24px; background:white; border-radius:16px; box-shadow:0 6px 20px rgba(0,0,0,.06); margin-bottom:18px; }
.card { background:white; padding:20px; border-radius:16px; box-shadow:0 8px 24px rgba(0,0,0,.06); margin-bottom:16px; }
.card-muted { background:#fbfcfe; border:1px solid #eef1f5; }
.kpi { text-align:center; }
.kpi h2 { margin:0; font-size:28px; }
.kpi span { font-size:13px; color:#6b7280; }
.badge { padding:6px 12px; border-radius:999px; font-size:12px; font-weight:600; color:white; }
.alert { padding:14px; border-radius:12px; background:#fff5f5; border:1px solid #ffd6d6; margin-bottom:10px; }
.stButton>button { border-radius:10px; font-weight:600; }
.footer { text-align:center; color:#9ca3af; font-size:12px; margin-top:32px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=30)
def cached_emails(token: str):
    return get_emails(token=token, limit=500)


# ===================== LOGIN / SIGNUP FLOW =====================
if not st.session_state.token:
    st.markdown("## 🔐 Secure Access")
    tab1, tab2 = st.tabs(["Login", "Create Workspace"])

    with tab1:
        email = st.text_input("Work Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login →", key="login_btn"):
            token = login(email, password)
            if token:
                st.session_state.token = token
                user = safe_get_current_user()
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("⚠️ Could not fetch user data. Try again.")

    with tab2:
        company = st.text_input("Company Name", key="signup_company")
        email = st.text_input("Work Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Create Account →", key="signup_btn"):
            token = signup(email, password, company)
            if token:
                st.session_state.token = token
                user = safe_get_current_user()
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("⚠️ Could not fetch user data. Try again.")

    st.stop()

# ===================== LOAD USER =====================
user = safe_get_current_user()
if not user:
    st.warning("🔐 Session expired. Please login again.")
    logout()
    st.stop()

token = st.session_state.token

# ===================== USER INFO =====================
role = user.get("role", "member")
plan = user.get("plan", "starter").lower()
workspace_name = user.get("workspace_name", "Workspace")

PLAN_COLOR = {"starter": "#3b82f6", "growth": "#f59e0b", "pro": "#10b981"}.get(plan, "#3b82f6")

# ===================== DATA =====================
# Uses the app's own session token (issued at login), not a Gmail
# credential -- the backend is the only thing that talks to Gmail
# directly (see backend/app/services/email_sync.py).
emails = cached_emails(token)
alerts = [e for e in emails if e.get("needs_followup")]

# ===================== TOP BAR =====================
st.markdown(f"""
<div class="topbar">
    <div>
        <h3 style="margin:0">💸 Revenue Recovery AI</h3>
        <span style="color:#6b7280">{workspace_name}</span>
    </div>
    <div>
        <span class="badge" style="background:{PLAN_COLOR}">{plan.upper()} PLAN</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ===================== SIDEBAR =====================
st.sidebar.markdown("### 📊 Workspace")
st.sidebar.markdown(f"**{user['email']}**")
st.sidebar.markdown("---")
st.sidebar.markdown(f"### 🚨 Alerts ({len(alerts)})")

for e in alerts[:10]:
    st.sidebar.markdown(
        f"<div class='alert'>⚠️ {format_snippet(e.get('subject', 'No subject'), 40)}</div>",
        unsafe_allow_html=True,
    )

st.sidebar.markdown("---")

MENU = {"Dashboard": "📊", "Recovery Pipeline": "🔁", "Analytics": "📈"}
if role == "admin":
    MENU["Settings"] = "⚙️"
MENU["Logout"] = "🚪"

page = st.sidebar.radio("Navigation", list(MENU.keys()), format_func=lambda x: f"{MENU[x]} {x}")

# ===================== PAGES =====================
if page == "Dashboard":
    render_dashboard(user, token)
elif page == "Recovery Pipeline":
    render_recovery_pipeline(user, token)
elif page == "Analytics":
    render_analytics(user, token)
elif page == "Settings":
    render_settings(user, token)
elif page == "Logout":
    logout()

# ===================== FOOTER =====================
st.markdown(
    f"<div class='footer'>© {datetime.datetime.now().year} Revenue Recovery AI · Enterprise SaaS</div>",
    unsafe_allow_html=True,
)
