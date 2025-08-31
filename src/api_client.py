"""Helper utilities for authenticated API requests from the Streamlit app."""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def auth_headers() -> dict[str, str]:
    """Return authorization headers using the stored Firebase ID token."""
    token = st.session_state.get("id_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def backend_url() -> str:
    """Return base URL for the backend service."""
    # Prefer Streamlit secrets; fallback to environment variable
    return (
        st.secrets.get("DEPLOYED_URL")
        if hasattr(st, "secrets") and "DEPLOYED_URL" in st.secrets
        else os.getenv("DEPLOYED_URL", "http://localhost:8000")
    )
