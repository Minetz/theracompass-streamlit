"""Patient streamlit page."""

import json
import os
from datetime import UTC, datetime, time

import requests
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from api_client import auth_headers, backend_url
from login import call_get_user_api
from markdown_loader import load_markdown
from styles import (
    CARD_STYLE,
    CHECKBOX_STYLE,
    DELETE_SESSION_BUTTON_STYLE,
    INPUT_STYLE,
    SELECT_STYLE,
    SMALL_CARD_STYLE,
    WHITE_BUTTON_STYLE,
    YELLOW_BUTTON_STYLE,
)


def call_transcription_api(
    user_id: str, patient_id: str, uploaded_audio_name: str, session_datetime: str
) -> dict:
    """Call the FastAPI process_audio endpoint with uploaded audio and user ID."""
    try:
        # Split file name into name and extension
        name_without_ext, extension = os.path.splitext(uploaded_audio_name)
        # Get test_audio_dir from environment variable
        test_audio_dir = os.getenv("TEST_AUDIO_DIR")
        if not test_audio_dir:
            raise ValueError("Missing environment variable TEST_AUDIO_DIR")
        if not os.path.isdir(test_audio_dir):
            raise FileNotFoundError(f"Invalid TEST_AUDIO_DIR, directory not found: {test_audio_dir}")
        # Open the audio file and fill in the files data
        audio_path = os.path.join(test_audio_dir, uploaded_audio_name)
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        with open(audio_path, "rb") as audio_file:
            uploaded_audio = audio_file.read()
        # Prepare the audio file and form data to send to the API
        files = {"audio_file": (name_without_ext, uploaded_audio, extension)}
        data = {
            "user_id": user_id,
            "patient_id": patient_id,
            "session_datetime": session_datetime,
        }

        # Send POST request to the process_audio endpoint
        response = requests.post(
            f"{backend_url()}/process_audio",
            files=files,
            data=data,
            headers=auth_headers(),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        # Catch and return any API or connection error
        return {"error": str(e)}
    except Exception as e:
        # Surface local validation errors clearly to the UI
        return {"error": str(e)}


def get_transcription_api_call(transcription_id: str) -> dict:
    """Call the API to get session details."""
    try:
        response = requests.get(
            f"{backend_url()}/get_transcription",
            params={"transcription_id": transcription_id},
            headers=auth_headers(),
        )
        response.raise_for_status()
        return json.loads(response.json())
    except requests.RequestException as e:
        return {"error": str(e)}


def call_delete_session_api(user_id: str, patient_id: str, session_id: str) -> dict:
    """Call API to delete a session."""
    try:
        resp = requests.delete(
            f"{backend_url()}/delete_session",
            params={
                "user_id": user_id,
                "patient_id": patient_id,
                "session_id": session_id,
            },
            headers=auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def call_delete_patient_api(user_id: str, patient_id: str) -> dict:
    """Call API to delete a patient."""
    try:
        resp = requests.delete(
            f"{backend_url()}/delete_patient",
            params={"user_id": user_id, "patient_id": patient_id},
            headers=auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def compute_session_analytics(session_id: str) -> dict:
    """Compute basic analytics for a session."""
    transcript = get_transcription_api_call(session_id)
    # if isinstance(transcript, str):
    #    transcript = json.loads(transcript)
    if "error" in transcript:
        return {"word_count": 0, "duration": 0}
    words = transcript["data"]["words"]
    duration = max((w["end"] for w in words), default=0)
    return {"word_count": len(words), "duration": duration}


def patient_page(patient_id: str):  # noqa: C901, PLR0912, PLR0915
    """Render a patient page."""
    st.markdown(load_markdown("login_style.md"), unsafe_allow_html=True)
    # Action bar: Back + Refresh (left), Delete Patient + My Account (right)
    action_left, action_right = st.columns([3, 2])
    with action_left:
        left1, left2, _left_spacer = st.columns([1, 1, 6])
        with left1, stylable_container(key="back_scope", css_styles=WHITE_BUTTON_STYLE):
            if st.button("Indietro"):
                st.session_state["page"] = "home_page"
                st.rerun()
        with left2, stylable_container(key="refresh_scope_patient", css_styles=WHITE_BUTTON_STYLE):
            if st.button("Aggiorna"):
                user_id = st.session_state.get("user_id")
                if user_id:
                    refreshed = call_get_user_api(user_id)
                    st.session_state["response"] = (
                        refreshed if isinstance(refreshed, dict) else json.loads(refreshed)
                    )
                    st.rerun()
    with action_right:
        _right_spacer, right1, right2 = st.columns([4, 2, 2])
        with right1, stylable_container(key="delete_patient_scope", css_styles=DELETE_SESSION_BUTTON_STYLE):
            if st.button("Elimina paziente", use_container_width=True):
                resp = call_delete_patient_api(st.session_state.get("user_id", ""), patient_id)
                if "error" in resp:
                    st.error(f"Eliminazione non riuscita: {resp['error']}")
                else:
                    st.success("Paziente eliminato")
                    st.session_state["page"] = "home_page"
                    st.rerun()
        with right2, stylable_container(key="account_scope", css_styles=WHITE_BUTTON_STYLE):
            if st.button("Il mio account", use_container_width=True):
                st.session_state["page"] = "account_page"
                st.rerun()

    # Display user id
    patients = st.session_state["response"]["patient_dir"]
    if patient_id in patients:
        patient = patients[patient_id]
    st.title(f"Paziente: {patient['name']}")
    st.write(f"ID paziente: {patient_id}")


    # New Session dialog (per Streamlit docs)
    @st.dialog("Nuova seduta")
    def new_session_dialog():
        # Card style inside dialog
        with stylable_container(key="new_session_card", css_styles=CARD_STYLE):
            # Demo / file selection (keeps existing logic)
            if os.getenv("MODE") == "demo":
                demo_dir = os.getenv("TEST_AUDIO_DIR") or ""
                audio_files: list[str] = []
                if not demo_dir:
                    st.error("TEST_AUDIO_DIR non è impostata. Definiscila nel file .env.")
                elif not os.path.isdir(demo_dir):
                    st.error(f"TEST_AUDIO_DIR non esiste: {demo_dir}")
                else:
                    try:
                        audio_files = [
                            f
                            for f in os.listdir(demo_dir)
                            if f.lower().endswith((".m4a", ".wav", ".mp3"))
                        ]
                    except OSError as e:  # permission or other fs errors
                        st.error(f"Impossibile elencare TEST_AUDIO_DIR ({demo_dir}): {e}")
                with stylable_container(key="new_session_select", css_styles=SELECT_STYLE):
                    selected_audio = st.selectbox(
                        "Seleziona un file audio",
                        audio_files if audio_files else ["(nessun file audio trovato)"]
                    )

            now = datetime.now(UTC)
            default_time = time(hour=now.hour)
            with stylable_container(key="new_session_datetime", css_styles=INPUT_STYLE):
                st.markdown("<br><br>", unsafe_allow_html=True)
                date_val = st.date_input("Data seduta", value=now.date())
                time_val = st.time_input("Ora seduta", value=default_time, step=3600)
            session_datetime = datetime.combine(date_val, time_val).isoformat(timespec="hours")

            st.markdown("<br>", unsafe_allow_html=True)
            with stylable_container(key="consent_checkbox", css_styles=CHECKBOX_STYLE):
                accept_processing = st.checkbox(
                    "Accetto il trattamento dei dati durante questa seduta", value=True
                )
            # Yellow action button
            with stylable_container(key="new_session_start_btn", css_styles=YELLOW_BUTTON_STYLE):
                if st.button("Avvia analisi", key="start_analysis_dialog"):
                    if not accept_processing:
                        st.warning("Accetta i termini di trattamento dei dati per continuare.")
                    else:
                        st.write("Invio audio per l'analisi…")
                        response_data = call_transcription_api(
                            user_id=st.session_state["user_id"],
                            patient_id=patient_id,
                            uploaded_audio_name=selected_audio,
                            session_datetime=session_datetime,
                        )
                        st.session_state["response"] = json.loads(
                            call_get_user_api(st.session_state["user_id"])  # refresh
                        )
                        if "error" in response_data:
                            st.error("Trascrizione non riuscita.")
                            st.text(response_data["error"])
                        else:
                            st.success("Trascrizione completata con successo.")
                            st.json(response_data)
                        st.rerun()  # closes dialog

    # Trigger button above sessions list
    with stylable_container(key="new_session_btn", css_styles=YELLOW_BUTTON_STYLE):
        if st.button("New Session", key="open_new_session"):
            new_session_dialog()


    # Display patient details
    if "response" in st.session_state:
        if "patient_dir" in st.session_state["response"]:
            patients = st.session_state["response"]["patient_dir"]
            if patient_id in patients:
                patient = patients[patient_id]
                sessions = patient["items"]
                session_stats = {}
                total_words = 0
                total_duration = 0
                for session_id in sessions:
                    stats = compute_session_analytics(session_id)
                    session_stats[session_id] = stats
                    total_words += stats["word_count"]
                    total_duration += stats["duration"]

                sorted_sessions = sorted(
                    sessions.items(),
                    key=lambda kv: kv[1].get("datetime", ""),
                    reverse=True,
                )

                with stylable_container(key="patient_analytics_card", css_styles=CARD_STYLE):
                    st.subheader("Sedute")
                    col1, col2, col3 = st.columns(3)

                    col1.metric("Sedute", len(sessions))
                    col2.metric("Parole totali", total_words)
                    col3.metric("Durata totale (s)", round(total_duration, 1))

                    for session_id, session in sorted_sessions:
                        stats = session_stats.get(session_id, {"word_count": 0, "duration": 0})
                        dt_str = session.get("datetime")
                        display_dt = (
                            datetime.fromisoformat(dt_str).strftime("%Y-%m-%d %H:00")
                            if dt_str
                            else "N/A"
                        )
                        with (
                            stylable_container(
                                key=f"session_card_{session_id}",
                                css_styles=SMALL_CARD_STYLE,
                            ),
                            st.expander(
                                f"{session.get('type', 'Sessione')} - {display_dt}",
                                expanded=True,
                            ),
                        ):
                            st.write(f"ID: {session_id}")
                            sc1, sc2 = st.columns(2)
                            sc1.metric("Words", stats["word_count"])
                            sc2.metric("Duration (s)", round(stats["duration"], 1))
                            btn_left, btn_right = st.columns([1, 1])
                            with btn_left:
                                with stylable_container(
                                    key=f"open_session_btn_{session_id}",
                                    css_styles=YELLOW_BUTTON_STYLE,
                                ):
                                    if st.button("Apri seduta", key=session_id):
                                        st.session_state["page"] = "session_page"
                                        st.session_state["selected_session_id"] = session_id
                                        st.rerun()
                            with btn_right:
                                with stylable_container(
                                    key=f"delete_session_btn_{session_id}",
                                    css_styles=DELETE_SESSION_BUTTON_STYLE,
                                ):
                                    if st.button("Elimina seduta", key=f"del_{session_id}"):
                                        resp = call_delete_session_api(
                                            st.session_state.get("user_id", ""),
                                            patient_id,
                                            session_id,
                                        )
                                        if "error" in resp:
                                            st.error(resp["error"])
                                        else:
                                            st.success("Seduta eliminata")
                                            st.rerun()
                            # Small space
                            st.markdown("<br>", unsafe_allow_html=True)

            else:
                st.error("Paziente non trovato.")
        else:
            st.error("Nessun dato del paziente disponibile. Crea prima un paziente.")
    else:
        st.error("Nessun dato del paziente disponibile. Crea prima un paziente.")
