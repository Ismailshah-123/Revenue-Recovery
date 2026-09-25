# ====================== components/tables.py ======================
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from utils.api import analyze_thread

st.markdown("""
<style>
.ag-theme-material {
    border-radius:14px;
    overflow:hidden;
    box-shadow:0 8px 24px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)


def render_leak_table(emails: list, token: str):
    st.markdown("### 🧯 Revenue Leak Detection")
    st.caption("Emails identified as potential revenue risks.")

    if not emails:
        st.success("No revenue leaks detected.")
        return

    df = pd.DataFrame([{
        "Subject": e.get("subject") or "No Subject",
        "Sender": e.get("sender") or "Unknown",
        "Risk Status": "⚠️ Needs Follow-up" if e.get("needs_followup") else "✅ Healthy",
        "AI Status": "Completed" if e.get("ai_insight") else "Pending",
        "Revenue Impact ($)": e.get("detected_value", 0),
        "Thread ID": e["thread_id"],
    } for e in emails])

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection("multiple", use_checkbox=True)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    gb.configure_column(
        "Revenue Impact ($)",
        type=["numericColumn"],
        cellStyle={"fontWeight": "bold", "color": "#E53935"},
    )
    grid_options = gb.build()

    grid = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme="material",
    )

    selected = grid["selected_rows"]

    if selected is not None and len(selected) > 0:
        st.info(f"{len(selected)} threads selected")
        if st.button("🧠 Run AI Analysis on Selected"):
            for row in selected.to_dict("records") if hasattr(selected, "to_dict") else selected:
                analyze_thread(token, row["Thread ID"])
            st.success("AI analysis completed successfully.")
            st.rerun()
