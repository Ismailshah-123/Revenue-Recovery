import streamlit as st
import datetime
import time
import threading

from utils.api import get_emails, analyze_thread
from utils.helpers import format_snippet, page_header
from utils.session import require_auth, get_token


# ================= AUTH =================
require_auth()
TOKEN = get_token()

# ================= HEADER =================
page_header(
    "⚙️ AI Recovery Pipeline",
    "End-to-end workflow for identifying, prioritizing, and recovering lost revenue using AI."
)

# ================= STYLES =================
st.markdown("""
<style>
.pipeline-card {
    padding:20px;
    margin-bottom:16px;
    border-radius:16px;
    background:linear-gradient(135deg,#ffffff,#f8fafc);
    box-shadow:0 8px 24px rgba(0,0,0,.08);
    transition:0.2s;
}
.pipeline-card:hover {
    transform:translateY(-4px);
}

.badge {
    padding:4px 12px;
    border-radius:20px;
    font-size:12px;
    font-weight:600;
    color:white;
}

.badge-risk { background:#E53935; }
.badge-safe { background:#43A047; }
.badge-ai { background:#1E88E5; }
.badge-done { background:#6D4C41; }

.stage {
    font-size:13px;
    font-weight:600;
    color:#546E7A;
}
</style>
""", unsafe_allow_html=True)

# ================= LOAD DATA =================
with st.spinner("⚡ Loading recovery pipelines..."):
    emails = get_emails(token=TOKEN, limit=50) or []

if not emails:
    st.info("No active recovery pipelines yet.")
    st.stop()

# ================= AI WORKER =================
def run_ai(thread_id, status_box):
    with status_box:
        st.info("🤖 AI processing started...")
    analyze_thread(thread_id)
    with status_box:
        st.success("✅ AI analysis completed")

# ================= PIPELINE SUMMARY =================
total = len(emails)
completed = len([e for e in emails if e.get("ai_insight")])
pending = total - completed

c1, c2, c3 = st.columns(3)
c1.metric("Total Pipelines", total)
c2.metric("AI Completed", completed)
c3.metric("Pending Review", pending)

st.progress(completed / total if total else 0)

st.markdown("---")

# ================= PIPELINE LIST =================
for e in emails:
    subject = format_snippet(e.get("subject", "No Subject"), 80)
    risk = e.get("needs_followup")
    ai_done = bool(e.get("ai_insight"))

    risk_badge = "badge-risk" if risk else "badge-safe"
    risk_text = "High Risk" if risk else "Low Risk"

    stage = "AI Completed" if ai_done else "Awaiting AI"
    stage_badge = "badge-done" if ai_done else "badge-ai"

    st.markdown(f"""
    <div class="pipeline-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <b>{subject}</b><br>
                <span class="stage">Stage: {stage}</span>
            </div>
            <span class="badge {risk_badge}">{risk_text}</span>
        </div>

        <div style="margin-top:10px;font-size:13px;">
            Sender: <b>{e.get("sender","Unknown")}</b> &nbsp;|&nbsp;
            AI Status: <span class="badge {stage_badge}">{'Done' if ai_done else 'Pending'}</span>
        </div>
    """, unsafe_allow_html=True)

    a1, a2 = st.columns([1, 1])
    status_box = st.empty()

    with a1:
        if not ai_done and st.button("🧠 Run AI Analysis", key=f"ai_{e['thread_id']}"):
            threading.Thread(
                target=run_ai,
                args=(e["thread_id"], status_box),
                daemon=True
            ).start()

    with a2:
        st.button("✔ Mark as Reviewed", key=f"done_{e['thread_id']}")

    st.markdown("</div>", unsafe_allow_html=True)

# ================= FOOTER =================
st.caption(f"Last updated • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
