# ====================== components/alerts.py ======================
import streamlit as st

st.markdown("""
<style>
.alert-card {
    padding:18px;
    margin-bottom:14px;
    border-radius:14px;
    background:linear-gradient(135deg,#ffffff,#f8fafc);
    box-shadow:0 6px 20px rgba(0,0,0,0.08);
    transition:0.2s;
}
.alert-card:hover { transform:translateY(-4px); }
.badge { padding:4px 10px; border-radius:20px; font-size:12px; font-weight:600; color:white; }
.badge-high { background:#E53935; }
.badge-low { background:#43A047; }
.alert-meta { font-size:13px; color:#546E7A; }
</style>
""", unsafe_allow_html=True)


def render_alerts(emails: list):
    st.markdown("### 🚨 Revenue Risk Alerts")
    st.caption("Threads that require immediate attention to prevent revenue loss.")

    alerts = [e for e in emails if e.get("needs_followup") and not e.get("ai_insight")]

    if not alerts:
        st.success("✅ No critical alerts. Revenue pipeline is healthy.")
        return

    for e in alerts:
        revenue_loss = e.get("detected_value", 0)
        st.markdown(f"""
        <div class="alert-card">
            <div style="display:flex;justify-content:space-between;">
                <b>{e.get('subject', 'No Subject')}</b>
                <span class="badge badge-high">High Risk</span>
            </div>
            <div class="alert-meta" style="margin-top:6px;">
                Sender: <b>{e.get('sender', 'Unknown')}</b><br>
                Potential Revenue Loss: <b>${revenue_loss:,}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✔ Mark as Resolved", key=f"resolve-{e['thread_id']}"):
            st.success("Alert marked as resolved.")
