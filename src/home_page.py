"""Home page."""

import json

import requests
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from framework_summary import TherapyFramework

from api_client import auth_headers, backend_url
from login import call_get_user_api
from markdown_loader import load_markdown
from styles import (
    CARD_STYLE,
    INPUT_STYLE,
    WHITE_BUTTON_STYLE,
    YELLOW_BUTTON_STYLE,
)


def call_new_patient(user_id: str, patient_name: str, framework: TherapyFramework) -> dict:
    """Call the FastAPI create_patient endpoint to create a new patient."""
    try:
        # Send POST request to the create_patient endpoint with user_id and patient_name
        response = requests.post(
            f"{backend_url()}/create_patient",
            data={
                "user_id": user_id,
                "patient_name": patient_name,
                "framework": framework.value,
            },
            headers=auth_headers(),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        # Catch and return any API or connection error
        return {"error": str(e)}


def home_page():  # noqa: C901, PLR0915
    """Render the home page."""
    st.markdown(load_markdown("login_style.md"), unsafe_allow_html=True)
    # Top navigation buttons
    back_col, _, refresh_col = st.columns([1, 8, 1])
    with back_col, stylable_container(key="back_scope", css_styles=WHITE_BUTTON_STYLE):
        if st.button("Esci"):
            st.session_state.pop("user_id", None)
            st.session_state.pop("response", None)
            st.rerun()
    with refresh_col, stylable_container(key="refresh_scope", css_styles=WHITE_BUTTON_STYLE):
        if st.button("Aggiorna"):
            user_id = st.session_state.get("user_id")
            if user_id:
                refreshed = call_get_user_api(user_id)
                st.session_state["response"] = (
                    refreshed if isinstance(refreshed, dict) else json.loads(refreshed)
                )
                st.rerun()
    st.title("Home")
    # Display user id
    if "user_id" in st.session_state:
        user_id = st.session_state["user_id"]
        st.write(f"ID utente: {user_id}")

    else:
        st.error("Non hai effettuato l'accesso. Accedi prima.")
        return

    # Ensure user response exists in session state
    if "response" not in st.session_state or not st.session_state["response"]:
        refreshed = call_get_user_api(user_id)
        st.session_state["response"] = (
            refreshed if isinstance(refreshed, dict) else json.loads(refreshed)
        )

    # Display patients
    with stylable_container(key="patient_list", css_styles=CARD_STYLE):
        # Section title for patients
        st.subheader("I tuoi pazienti")

        # Display each patient as an expander
        resp = st.session_state.get("response")
        if isinstance(resp, str):
            try:
                resp = json.loads(resp)
                st.session_state["response"] = resp
            except Exception:
                st.error("Formato dati utente non valido.")
                return

        if not isinstance(resp, dict):
            st.error("Dati utente mancanti o non validi.")
            return

        # Check if response contains patient data
        patients = resp.get("patient_dir", {}) or {}
        for patient in patients.values():
            with (
                stylable_container(key=patient["name"], css_styles=CARD_STYLE),
                st.expander(patient["name"], expanded=True),
            ):
                st.write(f"ID paziente: {patient['patient_id']}")
                st.write(f"Numero di elementi del paziente: {len(patient['items'])}")
                with stylable_container(
                    key=patient["name"] + "_button",
                    css_styles=WHITE_BUTTON_STYLE,
                ):
                    if st.button("Apri", key=patient["patient_id"]):
                        st.session_state["page"] = "patient_page"
                        st.session_state["selected_patient_id"] = patient["patient_id"]
                        st.rerun()

    @st.dialog("-")
    def new_patient_dialog():
        with stylable_container(key="modale", css_styles=CARD_STYLE):
            # Small space
            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(key="modale_patient_name", css_styles=INPUT_STYLE):
                name = st.text_input("Patient Name", key="patient_name_modal")
            # Framework selection
            with stylable_container(key="modale_framework", css_styles=INPUT_STYLE):
                framework = st.selectbox(
                    "Therapy Framework",
                    list(TherapyFramework),
                    format_func=lambda f: f.name.upper(),
                    key="framework_modal",
                )
            # Small space
            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(
                key="modale_new_patient_button",
                css_styles=YELLOW_BUTTON_STYLE,
            ):
                create_clicked = st.button("Create", key="create_patient_modal")

            if create_clicked:
                if name:
                    resp = call_new_patient(user_id, name, framework)
                    if "error" in resp:
                        st.error(f"Error creating patient: {resp['error']}")
                    else:
                        st.success(f"Patient '{name}' created successfully!")
                        # Refresh user data
                        refreshed = call_get_user_api(user_id)
                        st.session_state["response"] = (
                            refreshed if isinstance(refreshed, dict) else json.loads(refreshed)
                        )
                        st.rerun()  # closes the dialog per docs
                else:
                    st.error("Please enter a patient name.")

    # New Patient button (opens modal)
    with stylable_container(key="new_patient_btn", css_styles=YELLOW_BUTTON_STYLE):
        if st.button("New Patient", key="open_new_patient"):
            new_patient_dialog()
