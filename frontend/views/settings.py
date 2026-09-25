# ====================== views/settings.py ======================
import datetime

import streamlit as st

from utils.api import create_checkout_session
from utils.helpers import page_header


def render_settings(user: dict, token: str):
    page_header(
        "💳 Subscription & Billing",
        "Manage your plan, usage limits, and premium AI features.",
    )

    st.markdown("""
    <style>
    .plan-card {
        padding:20px;
        border-radius:16px;
        background:linear-gradient(135deg,#ffffff,#f8fafc);
        box-shadow:0 8px 24px rgba(0,0,0,.08);
        margin-bottom:20px;
    }
    .plan-name { font-size:20px; font-weight:700; }
    .feature { color:#455A64; font-size:14px; }
    </style>
    """, unsafe_allow_html=True)

    current_plan = user.get("plan", "starter")

    st.markdown("<div class='plan-card'>", unsafe_allow_html=True)
    st.markdown("<div class='plan-name'>Current Plan</div>", unsafe_allow_html=True)
    st.text_input("Plan", current_plan.upper(), disabled=True, label_visibility="collapsed")
    st.markdown("""
    <ul class="feature">
    <li>Email monitoring & alerts</li>
    <li>AI-powered revenue-risk analysis</li>
    <li>Recovery pipeline tracking</li>
    </ul>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 🚀 Upgrade Your Plan")
    plan_options = [p for p in ["starter", "growth", "pro"] if p != current_plan]

    if not plan_options:
        st.info("You're already on our top plan.")
    else:
        plan = st.selectbox("Choose a plan", plan_options, format_func=lambda x: x.upper())

        if st.button("Proceed to Secure Checkout"):
            checkout_url = create_checkout_session(token, plan)
            if checkout_url:
                st.success("Checkout session created")
                st.markdown(f"[Open Checkout]({checkout_url})")
            else:
                st.error("Failed to initiate checkout. Please try again.")

    st.caption(f"Last updated • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
