import streamlit as st
import datetime

from components.kpis import render_kpis
from components.tables import render_leak_table
from components.alerts import render_alerts
from utils.helpers import page_header, empty_state
from utils.api import get_emails


def render_dashboard(user):
    # ===================== HEADER =====================
    page_header(
        "🛡️ Revenue Command Center",
        "Real-time visibility into revenue risks, AI recoveries, and operational health."
    )

    # ===================== GLOBAL STYLES =====================
    st.markdown("""
    <style>
    .saas-card {
        background: linear-gradient(135deg, #ffffff, #f9fafb);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
        border: 1px solid #eef2f7;
    }
    .saas-card h3 {
        margin-top: 0;
    }
    .muted {
        color: #6b7280;
        font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ===================== DATA =====================
    token = st.session_state.get("token")
    emails = get_emails(token, limit=500) if token else []

    if not emails:
        empty_state(
            "No email data available yet. Connect your inbox or wait for ingestion.",
            icon="📭"
        )
        return

    at_risk = [e for e in emails if e.get("needs_followup")]
    ai_completed = [e for e in emails if e.get("ai_insight")]
    total_value = sum(e.get("detected_value", 0) for e in emails)

    # ===================== EXECUTIVE SUMMARY =====================
    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    st.markdown("### 📊 Executive Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Conversations", len(emails))
    c2.metric("At-Risk Threads", len(at_risk))
    c3.metric("AI Analyzed", len(ai_completed))
    c4.metric("Detected Revenue ($)", f"{total_value:,}")

    st.markdown("<p class='muted'>High-level snapshot for founders & revenue leaders</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ===================== ALERTS =====================
    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    st.markdown("### 🚨 Priority Alerts")

    if at_risk:
        render_alerts(user)
    else:
        empty_state("No critical revenue risks detected 🎉", icon="✅")

    st.markdown("</div>", unsafe_allow_html=True)

    # ===================== KPIs =====================
    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    st.markdown("### 💡 Key Performance Indicators")
    render_kpis()
    st.markdown("</div>", unsafe_allow_html=True)

    # ===================== REVENUE LEAK TABLE =====================
    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    st.markdown("### 📋 Revenue Leak Intelligence")
    st.markdown(
        "<p class='muted'>AI-detected risks with estimated revenue impact</p>",
        unsafe_allow_html=True
    )

    emails = render_leak_table(user)

    st.markdown("</div>", unsafe_allow_html=True)

    # ===================== PIPELINE HEALTH =====================
    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    st.markdown("### 🔧 Recovery Pipeline Health")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pipelines", len(emails))
    c2.metric(
        "Active Pipelines",
        len([e for e in emails if not e.get("ai_insight")])
    )
    c3.metric(
        "Completed by AI",
        len([e for e in emails if e.get("ai_insight")])
    )

    st.markdown(
        "<p class='muted'>Tracks operational progress of AI-driven recovery workflows</p>",
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ===================== FOOTER =====================
    st.caption(
        f"Last updated • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
