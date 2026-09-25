# ====================== utils/auth.py ======================
import requests
import streamlit as st

BACKEND_URL = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")
TIMEOUT = 10


# ===================== SESSION =====================
def get_token():
    return st.session_state.get("token")


def is_authenticated():
    return bool(get_token())


# ===================== LOGIN =====================
def login(email, password):
    with st.spinner("Authenticating..."):
        try:
            res = requests.post(
                f"{BACKEND_URL}/api/auth/login",
                json={"email": email, "password": password},
                timeout=TIMEOUT,
            )
            res.raise_for_status()
            data = res.json()
            st.session_state.token = data["access_token"]
            st.session_state.refresh_token = data.get("refresh_token")
            return data["access_token"]

        except requests.RequestException:
            st.error("Invalid email or password")
            return None


# ===================== SIGNUP =====================
def signup(email, password, company):
    with st.spinner("Creating workspace..."):
        try:
            res = requests.post(
                f"{BACKEND_URL}/api/auth/signup",
                json={"email": email, "password": password, "company": company},
                timeout=TIMEOUT,
            )
            res.raise_for_status()
            data = res.json()
            st.session_state.token = data["access_token"]
            st.session_state.refresh_token = data.get("refresh_token")
            return data["access_token"]

        except requests.RequestException:
            st.error("Signup failed. Please retry.")
            return None


# ===================== LOGOUT =====================
def logout():
    st.session_state.clear()
    st.success("You have been logged out")
    st.stop()
