"""Account page for user details and account management."""

import requests
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from api_client import auth_headers, backend_url
from markdown_loader import load_markdown
from styles import (
    CARD_STYLE,
    INPUT_STYLE,
    WHITE_BUTTON_STYLE,
    YELLOW_BUTTON_STYLE,
)


def call_delete_user_api(user_id: str) -> dict:
    """Call the API to delete the current user."""
    try:
        response = requests.delete(
            f"{backend_url()}/delete_user",
            params={"user_id": user_id},
            headers=auth_headers(),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:  # pragma: no cover - network errors
        return {"error": str(e)}


def account_page():
    """Render the account page."""
    st.markdown(load_markdown("login_style.md"), unsafe_allow_html=True)
    nav_left, _, _ = st.columns([1, 8, 1])
    with nav_left, stylable_container(key="back_scope_account", css_styles=WHITE_BUTTON_STYLE):
        if st.button("Indietro"):
            st.session_state["page"] = "patient_page"
            st.rerun()

    st.title("Il mio account")

    if "response" in st.session_state:
        user_info = st.session_state.get("response", {})
        with stylable_container(key="account_card", css_styles=CARD_STYLE):
            st.subheader("Dettagli utente")
            st.write(f"Nome utente: {user_info.get('username', '')}")
            st.write(f"Email: {user_info.get('email', '')}")
            st.write(f"Abbonamento: {user_info.get('user_subscription', '')}")
            st.write(f"ID utente: {user_info.get('user_id', '')}")
            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(key="delete_btn", css_styles=YELLOW_BUTTON_STYLE):
                if st.button("Elimina account", key="open_delete_account"):
                    delete_dialog()
    else:
        st.error("Informazioni utente non disponibili.")


@st.dialog("Elimina account")
def delete_dialog():
    """Dialog to confirm account deletion."""
    with stylable_container(key="delete_card", css_styles=CARD_STYLE):
        st.warning("Questa azione eliminerà definitivamente il tuo account.")
        with stylable_container(key="uid_input_delete", css_styles=INPUT_STYLE):
            uid = st.text_input("Digita il tuo UID per confermare")
        with stylable_container(key="confirm_delete_btn", css_styles=YELLOW_BUTTON_STYLE):
            if st.button("Conferma eliminazione"):
                if uid == st.session_state.get("user_id"):
                    resp = call_delete_user_api(uid)
                    if "error" in resp:
                        st.error(f"Eliminazione non riuscita: {resp['error']}")
                    else:
                        st.success("Account eliminato con successo")
                        st.session_state.pop("user_id", None)
                        st.session_state.pop("response", None)
                        st.session_state["page"] = "home_page"
                        st.rerun()
                else:
                    st.error("L'UID non corrisponde.")
