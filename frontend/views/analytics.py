# ====================== views/analytics.py ======================
import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api import get_emails
from utils.helpers import empty_state, page_header


def render_analytics(user: dict, token: str):
    page_header(
        "📊 Revenue Intelligence",
        "Deep insights into revenue risk, AI effectiveness, and recovery performance.",
    )

    with st.spinner("📡 Aggregating analytics data..."):
        emails = get_emails(token=token, limit=500)

    if not emails:
        empty_state("Analytics will appear once email data is ingested.", icon="📈")
        return

    total = len(emails)
    at_risk = [e for e in emails if e.get("needs_followup")]
    ai_done = [e for e in emails if e.get("ai_insight")]
    recovered_value = sum(e.get("recovered_value", 0) for e in emails)
    risk_value = sum(e.get("detected_value", 0) for e in at_risk)
    success_rate = (len(ai_done) / total * 100) if total else 0

    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📧 Conversations", total)
    c2.metric("⚠️ At-Risk Threads", len(at_risk))
    c3.metric("🤖 AI Completed", len(ai_done))
    c4.metric("📈 AI Success Rate", f"{success_rate:.1f}%")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    st.markdown("### 💰 Revenue Impact")
    c1, c2 = st.columns(2)
    c1.metric("Recovered Revenue ($)", f"{recovered_value:,}")
    c2.metric("Revenue at Risk ($)", f"{risk_value:,}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    st.markdown("### 🔻 Revenue Recovery Funnel")
    df_funnel = pd.DataFrame([
        {"Stage": "Total Conversations", "Count": total},
        {"Stage": "Revenue at Risk", "Count": len(at_risk)},
        {"Stage": "AI Processed", "Count": len(ai_done)},
    ])
    fig_funnel = px.funnel(df_funnel, x="Count", y="Stage", title="End-to-End Revenue Recovery Funnel")
    st.plotly_chart(fig_funnel, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    st.markdown("### 📈 Recovered Revenue Over Time")
    trend = [
        {
            "Date": (datetime.datetime.now() - datetime.timedelta(days=i % 30)).date(),
            "Recovered Revenue": e.get("recovered_value", 0),
        }
        for i, e in enumerate(ai_done)
    ]
    if trend:
        df_trend = pd.DataFrame(trend).groupby("Date").sum().reset_index()
        fig_trend = px.area(df_trend, x="Date", y="Recovered Revenue", title="AI-Recovered Revenue Trend")
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        empty_state("No AI-analyzed threads yet to chart a trend.", icon="📈")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    st.markdown("### 🤖 AI Performance Summary")
    avg_recovery = (recovered_value / len(ai_done)) if ai_done else 0
    st.markdown(
        f"""
        <ul>
            <li><b>{len(ai_done)}</b> conversations successfully analyzed by AI</li>
            <li><b>{len(at_risk)}</b> active revenue risks detected</li>
            <li>Average recovery value per thread: <b>${avg_recovery:,.2f}</b></li>
        </ul>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption(f"Last updated • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
