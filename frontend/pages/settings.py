import streamlit as st
import requests
import datetime

from utils.auth import get_token
from utils.helpers import page_header


# ================= HEADER =================
page_header(
    "💳 Subscription & Billing",
    "Manage your plan, usage limits, and premium AI features."
)

BACKEND = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")
token = get_token()
headers = {"Authorization": f"Bearer {token}"}

# ================= STYLES =================
st.markdown("""
<style>
.plan-card {
    padding:20px;
    border-radius:16px;
    background:linear-gradient(135deg,#ffffff,#f8fafc);
    box-shadow:0 8px 24px rgba(0,0,0,.08);
    margin-bottom:20px;
}
.plan-name {
    font-size:20px;
    font-weight:700;
}
.feature {
    color:#455A64;
    font-size:14px;
}
.upgrade {
    background:#1976D2;
    color:white;
    padding:10px 18px;
    border-radius:10px;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# ================= CURRENT PLAN =================
st.markdown("<div class='plan-card'>", unsafe_allow_html=True)
st.markdown("<div class='plan-name'>Current Plan</div>", unsafe_allow_html=True)
current_plan = st.text_input("Plan", "Starter", disabled=True)
st.markdown("""
<ul class="feature">
<li>Email monitoring & alerts</li>
<li>Basic AI analysis</li>
<li>Limited pipelines</li>
</ul>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ================= UPGRADE =================
st.markdown("### 🚀 Upgrade Your Plan")

plan = st.selectbox(
    "Choose a plan",
    ["starter", "growth", "pro"],
    format_func=lambda x: x.upper()
)

if st.button("Proceed to Secure Checkout"):
    with st.spinner("Redirecting to checkout..."):
        r = requests.post(
            f"{BACKEND}/billing/create-checkout",
            params={"plan": plan},
            headers=headers
        )
        if r.ok:
            st.success("Checkout session created")
            st.markdown(f"[Open Checkout]({r.json()['checkout_url']})")
        else:
            st.error("Failed to initiate checkout. Please try again.")

# ================= FOOTER =================
st.caption(f"Last updated • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
