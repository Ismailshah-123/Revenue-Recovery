# ====================== utils/helpers.py ======================
import streamlit as st


def format_snippet(text: str, max_len: int = 120):
    if not text:
        return ""
    return text if len(text) <= max_len else text[:max_len] + "…"


def status_badge(status: str):
    colors = {
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "pending": "#3B82F6",
        "recovered": "#22C55E",
        "at risk": "#EF4444",
    }
    color = colors.get(status.lower(), "#6B7280")

    return f"""
    <span style="
        background:{color};
        padding:6px 14px;
        border-radius:999px;
        color:white;
        font-size:12px;
        font-weight:600;
    ">
        {status.upper()}
    </span>
    """


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="margin-bottom:24px">
        <h1 style="margin-bottom:4px">{title}</h1>
        <p style="color:#6b7280">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def empty_state(message: str, icon="ℹ️"):
    st.markdown(f"""
    <div style="
        padding:24px;
        border-radius:16px;
        background:#f9fafb;
        border:1px dashed #e5e7eb;
        text-align:center;
        color:#6b7280;
    ">
        <h3>{icon}</h3>
        <p>{message}</p>
    </div>
    """, unsafe_allow_html=True)
