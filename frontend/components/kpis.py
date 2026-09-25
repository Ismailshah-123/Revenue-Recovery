# ====================== components/kpis.py ======================
import pandas as pd
import plotly.express as px
import streamlit as st

st.markdown("""
<style>
.kpi-card {
    padding:20px;
    border-radius:16px;
    background:linear-gradient(135deg,#ffffff,#f8fafc);
    box-shadow:0 8px 24px rgba(0,0,0,0.08);
    transition:0.2s;
}
.kpi-card:hover { transform:translateY(-4px); }
.kpi-title { font-size:14px; color:#607D8B; }
.kpi-value { font-size:28px; font-weight:700; }
</style>
""", unsafe_allow_html=True)


def render_kpis(emails: list):
    st.markdown("### 📊 Revenue Intelligence KPIs")

    total_at_risk = sum(e.get("detected_value", 0) for e in emails if e.get("needs_followup"))
    recovered = sum(e.get("recovered_value", 0) for e in emails)
    followups_needed = len([e for e in emails if e.get("needs_followup")])

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Revenue at Risk</div>
            <div class="kpi-value">${total_at_risk:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Recovered by AI</div>
            <div class="kpi-value">${recovered:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Follow-ups Required</div>
            <div class="kpi-value">{followups_needed}</div>
        </div>
        """, unsafe_allow_html=True)

    df = pd.DataFrame([{
        "Thread": (e.get("subject") or "")[:30],
        "At Risk": e.get("detected_value", 0) if e.get("needs_followup") else 0,
        "Recovered": e.get("recovered_value", 0),
    } for e in emails])

    if not df.empty:
        fig = px.bar(
            df,
            x="Thread",
            y=["At Risk", "Recovered"],
            title="Revenue Risk vs AI Recovery",
            template="plotly_white",
        )
        fig.update_layout(height=420, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
