"""Login and create users page."""

import json

import requests
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from firebase_handler import (
    create_user as firebase_create_user,
)
from firebase_handler import (
    init_firebase,
    send_password_reset_email,
    sign_in_with_email_and_password,
)
from api_client import auth_headers, backend_url
from markdown_loader import load_markdown
from styles import (
    CARD_STYLE,
    INPUT_STYLE,
    WHITE_BUTTON_STYLE,
    YELLOW_BUTTON_STYLE,
)


# main function to run the Streamlit app
def login(user_id: str = ""):  # noqa: C901, PLR0915
    """Run the login."""
    init_firebase()
    if user_id:
        response = call_get_user_api(user_id)
        if "error" in response:
            st.error(response["error"])
        else:
            st.session_state["user_id"] = user_id
            st.session_state["response"] = response
            st.rerun()
    st.markdown(load_markdown("login_style.md"), unsafe_allow_html=True)
    st.title("Emanuense")

    # Center column for login form
    col = st.columns([1, 1, 1])[1]

    @st.dialog("Registrati")
    def register_dialog() -> None:
        with stylable_container(key="register_card", css_styles=CARD_STYLE):
            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(key="reg_email", css_styles=INPUT_STYLE):
                reg_email = st.text_input("Email", key="reg_email_input")
            with stylable_container(key="reg_password", css_styles=INPUT_STYLE):
                reg_password = st.text_input("Password", type="password", key="reg_password_input")
            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(key="reg_button", css_styles=YELLOW_BUTTON_STYLE):
                if st.button("Crea", key="create_account"):
                    try:
                        firebase_create_user(reg_email, reg_password)
                        st.success("Account creato")
                    except Exception as e:
                        st.error(f"Errore durante la creazione dell'utente: {e}")

    @st.dialog("Reimposta password")
    def forgot_dialog() -> None:
        with stylable_container(key="forgot_card", css_styles=CARD_STYLE):
            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(key="forgot_email", css_styles=INPUT_STYLE):
                reset_email = st.text_input(
                    "Email",
                    key="reset_email_input",
                    placeholder="Email",
                )
            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(key="forgot_button", css_styles=YELLOW_BUTTON_STYLE):
                if st.button("Invia", key="send_reset"):
                    try:
                        send_password_reset_email(reset_email)
                        st.success("Link di reset inviato")
                    except Exception as e:
                        st.error(f"Errore durante l'invio dell'email di reset: {e}")

    with col:  # noqa: SIM117
        # Stylable container gives us a white "card" with padding and shadow
        with stylable_container(key="login_card", css_styles=CARD_STYLE):
            st.markdown("### Accesso")
            with stylable_container(key="email_input_scope", css_styles=INPUT_STYLE):
                email = st.text_input(
                    "Email",
                    label_visibility="collapsed",
                    placeholder="Email",
                )
            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(key="password_input_scope", css_styles=INPUT_STYLE):
                password = st.text_input(
                    "Password",
                    type="password",
                    label_visibility="collapsed",
                    placeholder="Password",
                )

            # Small empty separator
            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(key="acc_button_scope", css_styles=YELLOW_BUTTON_STYLE):
                if st.button("Accedi", use_container_width=True):
                    try:
                        # Authenticate with Firebase and store the ID token for API calls
                        auth_data = sign_in_with_email_and_password(email, password)
                        st.session_state["user_id"] = auth_data["localId"]
                        st.session_state["id_token"] = auth_data.get("idToken")
                        st.session_state["response"] = call_get_user_api(auth_data["localId"])
                        st.success("Accesso effettuato!")
                        st.rerun()
                    except Exception:
                        st.error("Errore durante l'autenticazione")

            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(key="forgot_button_scope", css_styles=WHITE_BUTTON_STYLE):
                if st.button("Password dimenticata", use_container_width=True):
                    forgot_dialog()
            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(key="register_scope", css_styles=WHITE_BUTTON_STYLE):
                if st.button("Registrati", use_container_width=True):
                    register_dialog()


def call_get_user_api(user_id: str) -> dict:
    """Call the FastAPI get_user endpoint with the user ID to retrieve user object."""
    try:
        # Send GET request to the get_user endpoint with user_id as query parameter
        response = requests.get(
            f"{backend_url()}/get_user",
            params={"user_id": user_id},
            headers=auth_headers(),
        )
        response.raise_for_status()
        return json.loads(response.text)
    except requests.RequestException as e:
        # Catch and return any API or connection error
        return {"error": str(e)}
