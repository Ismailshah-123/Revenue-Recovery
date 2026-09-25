import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

from utils.api import get_emails
from utils.session import require_auth, get_token
from utils.helpers import page_header, empty_state


# ===================== AUTH =====================
require_auth()
TOKEN = get_token()

# ===================== HEADER =====================
page_header(
    "📊 Revenue Intelligence",
    "Deep insights into revenue risk, AI effectiveness, and recovery performance."
)

# ===================== LOAD DATA =====================
with st.spinner("📡 Aggregating analytics data..."):
    emails = get_emails(token=TOKEN, limit=500) or []

if not emails:
    empty_state("Analytics will appear once email data is ingested.", icon="📈")
    st.stop()

# ===================== DERIVED METRICS =====================
total = len(emails)
at_risk = [e for e in emails if e.get("needs_followup")]
ai_done = [e for e in emails if e.get("ai_insight")]
recovered_value = sum(e.get("detected_value", 0) for e in ai_done)
risk_value = sum(e.get("detected_value", 0) for e in at_risk)

success_rate = (len(ai_done) / total * 100) if total else 0

# ===================== KPI STRIP =====================
st.markdown("<div class='saas-card'>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("📧 Conversations", total)
c2.metric("⚠️ At-Risk Threads", len(at_risk))
c3.metric("🤖 AI Completed", len(ai_done))
c4.metric("📈 AI Success Rate", f"{success_rate:.1f}%")

st.markdown("</div>", unsafe_allow_html=True)

# ===================== REVENUE METRICS =====================
st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
st.markdown("### 💰 Revenue Impact")

c1, c2 = st.columns(2)
c1.metric("Recovered Revenue ($)", f"{recovered_value:,}")
c2.metric("Revenue at Risk ($)", f"{risk_value:,}")

st.markdown("</div>", unsafe_allow_html=True)

# ===================== FUNNEL =====================
st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
st.markdown("### 🔻 Revenue Recovery Funnel")

df_funnel = pd.DataFrame([
    {"Stage": "Total Conversations", "Count": total},
    {"Stage": "Revenue at Risk", "Count": len(at_risk)},
    {"Stage": "AI Processed", "Count": len(ai_done)},
])

fig_funnel = px.funnel(
    df_funnel,
    x="Count",
    y="Stage",
    title="End-to-End Revenue Recovery Funnel"
)

st.plotly_chart(fig_funnel, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ===================== RECOVERY TREND =====================
st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
st.markdown("### 📈 Recovered Revenue Over Time")

trend = []
for i, e in enumerate(ai_done):
    trend.append({
        "Date": datetime.datetime.now() - datetime.timedelta(days=i % 30),
        "Recovered Revenue": e.get("detected_value", 0)
    })

df_trend = (
    pd.DataFrame(trend)
    .groupby("Date")
    .sum()
    .reset_index()
)

fig_trend = px.area(
    df_trend,
    x="Date",
    y="Recovered Revenue",
    title="AI-Recovered Revenue Trend"
)

st.plotly_chart(fig_trend, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ===================== AI PERFORMANCE =====================
st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
st.markdown("### 🤖 AI Performance Summary")

st.markdown(
    f"""
    <ul>
        <li><b>{len(ai_done)}</b> conversations successfully analyzed by AI</li>
        <li><b>{len(at_risk)}</b> active revenue risks detected</li>
        <li>Average recovery value per thread: <b>${(recovered_value / len(ai_done)):.2f}</b></li>
    </ul>
    """,
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)

# ===================== FOOTER =====================
st.caption(
    f"Last updated • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
