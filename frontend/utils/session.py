import streamlit as st

def require_auth():
    if "user" not in st.session_state or not st.session_state.get("token"):
        st.warning("🔐 Session expired. Please login again.")
        st.stop()   # ⛔ STOP execution — NO logout here

def get_token():
    return st.session_state.get("token")
