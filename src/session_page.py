"""Session streamlit page."""

import json
from typing import Any

import requests
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from api_client import auth_headers, backend_url
from login import call_get_user_api
from markdown_loader import load_markdown
from styles import (
    CARD_STYLE,
    DISCLAIMER_STYLE,
    WHITE_BUTTON_STYLE,
    DELETE_SESSION_BUTTON_STYLE,
)


# Placeholder function for changing the speaker
def change_speaker_callback(group_index):
    """Change the speaker for a group."""
    st.info(f"Cambia parlante per il gruppo {group_index} (funzione segnaposto)")


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


def compute_activity_data(words, interval=60):
    """Return word-count data binned by time interval.

    Parameters
    ----------
    words:
        List of word dictionaries containing ``start`` timestamps.
    interval:
        Size of each time bin in seconds. Defaults to 60 seconds.
    """
    if not words:
        return []
    starts = [w.get("start") for w in words if w.get("start") is not None]
    if not starts:
        return []
    last_time = max(starts)
    bins = int(last_time // interval) + 1
    counts = [0] * bins
    for start in starts:
        idx = int(start // interval)
        counts[idx] += 1
    data = [{"time": i * interval, "words": counts[i]} for i in range(bins)]
    return data


def display_activity_chart(transcript):
    """Display a simple activity chart and basic session analytics."""
    words = transcript.get("data", {}).get("words", [])
    data = compute_activity_data(words)
    if not data:
        st.write("Nessun dato di attività disponibile.")
        return
    total_words = len(words)
    total_duration = max((w.get("end", 0) for w in words), default=0)
    try:  # Import locally to avoid hard dependency during tests
        import altair as alt
    except ModuleNotFoundError:  # pragma: no cover - chart is optional
        st.write("Altair è necessario per visualizzare il grafico dell'attività.")
        return
    chart = (
        alt.Chart(alt.Data(values=data))
        .mark_area(
            opacity=0.3,
            line={"color": "#ffd400", "size": 2},
            color="#ffd400",
        )
        .encode(
            x=alt.X("time:Q", title="Time (s)"),
            y=alt.Y("words:Q", title="Word count"),
        )
        .properties(height=200)
        .configure_axis(labelColor="#000", titleColor="#000")
        .configure_view(strokeWidth=0)
        .configure(background="#ffffff")
    )
    st.markdown("<div></div>", unsafe_allow_html=True)  # ensure CSS scope is active
    st.subheader("Attività della seduta")
    col1, col2 = st.columns(2)
    col1.metric("Parole", total_words)
    col2.metric("Durata (s)", round(total_duration, 1))
    st.altair_chart(chart, use_container_width=True)


# Helper function to group messages by speaker
def group_messages_by_speaker(words):
    """Return a list of dicts."""
    if not words:
        return []
    groups = []
    current_speaker = words[0].get("speaker_id", "unknown")
    current_text = words[0]["word"]
    group_start = words[0].get("start")
    group_end = words[0].get("end")
    for w in words[1:]:
        speaker = w.get("speaker_id", "unknown")
        word_text = w["word"]
        word_start = w.get("start")
        word_end = w.get("end")
        if speaker == current_speaker:
            current_text += " " + word_text
            # Update group_end to the current word's end time
            group_end = word_end
        else:
            groups.append(
                {
                    "speaker": current_speaker,
                    "text": current_text.strip(),
                    "start_time": group_start,
                    "end_time": group_end,
                }
            )
            current_speaker = speaker
            current_text = word_text
            group_start = word_start
            group_end = word_end
    # Append the last group
    groups.append(
        {
            "speaker": current_speaker,
            "text": current_text.strip(),
            "start_time": group_start,
            "end_time": group_end,
        }
    )
    return groups


# New function: display conversation as a highlighted transcript
def display_grouped_chat(transcript, epi_summary):
    """Display the conversation as a highlighted transcript aligned with episodic summaries."""
    words = transcript.get("data", {}).get("words", [])
    if not words:
        st.write("Nessun dato di conversazione disponibile.")
        return
    groups = group_messages_by_speaker(words)
    st.subheader("Conversazione per riassunti episodici")
    if not epi_summary:
        st.write("Nessun riassunto episodico disponibile.")
        summaries = []
    else:
        summaries = epi_summary.get("summary_list", [])
    current_index = 0
    for idx, epi in enumerate(summaries):
        summary_text = epi.get("summary", "")
        end_time = float(epi.get("end_position", "0"))

        template = load_markdown("episodic_summary_template.md")
        with stylable_container(key=f"summary_card_{idx}", css_styles=CARD_STYLE):
            st.markdown(template.format(summary_text=summary_text))
            with st.expander("Mostra conversazione correlata", expanded=False):
                # Build a single markdown string with words colored by speaker
                def _esc(word: str) -> str:
                    for ch in ["\\", "]", "["]:
                        word = word.replace(ch, f"\\{ch}")
                    return word

                colored_parts: list[str] = []
                start_idx = current_index
                while current_index < len(groups):
                    group = groups[current_index]
                    group_end = group.get("end_time", 0)
                    if group_end and group_end > end_time:
                        break
                    speaker = str(group.get("speaker", "")).lower()
                    # st.write(
                    #    f"Speaker: {speaker} | Start: {group.get('start_time', 'N/A')} |
                    # End: {group_end}"
                    # )
                    color = "blue" if "therap" in speaker else "green"
                    text = group.get("text", "")
                    for raw in text.split():
                        colored_parts.append(f":{color}[{_esc(raw)}]")  # noqa: PERF401
                    current_index += 1

                if current_index == start_idx:
                    st.write("Nessuna conversazione per questo riassunto.")
                else:
                    st.markdown(" ".join(colored_parts))


def session_page(session_id: str):
    """Render a session page."""
    # Apply shared styles
    st.markdown(load_markdown("login_style.md"), unsafe_allow_html=True)

    nav_left, _, nav_refresh, nav_delete = st.columns([1, 6, 1, 1])
    with nav_left:  # noqa: SIM117
        with stylable_container(key="back_scope_session", css_styles=WHITE_BUTTON_STYLE):
            if st.button("Indietro"):
                st.session_state["page"] = "patient_page"
                st.rerun()
    with nav_refresh:  # noqa: SIM117
        with stylable_container(key="refresh_scope_session", css_styles=WHITE_BUTTON_STYLE):
            if st.button("Aggiorna"):
                user_id = st.session_state.get("user_id")
                if user_id:
                    refreshed = call_get_user_api(user_id)
                    st.session_state["response"] = (
                        refreshed if isinstance(refreshed, dict) else json.loads(refreshed)
                    )
    with nav_delete:  # noqa: SIM117
        with stylable_container(key="delete_scope_session", css_styles=DELETE_SESSION_BUTTON_STYLE):
            if st.button("Elimina"):
                user_id = st.session_state.get("user_id", "")
                patient_id = st.session_state.get("selected_patient_id", "")
                resp = call_delete_session_api(user_id, patient_id, session_id)
                if "error" in resp:
                    st.error(resp["error"])
                else:
                    st.success("Seduta eliminata")
                    st.session_state["page"] = "patient_page"
                    st.rerun()
                    st.rerun()

    st.title("Pagina della seduta")

    with stylable_container(key="session_disclaimer", css_styles=DISCLAIMER_STYLE):
        st.markdown(
            "This page displays data generated from automated processing of session recordings, "
            "including transcription, summarization, and analytics. Please review all results "
            "for accuracy before use."
        )

    if session_id:
        epi_summary = json.loads(get_epi_summary_api_call(session_id))
        transcript = json.loads(get_transcription_api_call(session_id))
        st.write(f"Session ID: {session_id}")

        with stylable_container(key="session_activity_card", css_styles=CARD_STYLE):
            display_activity_chart(transcript)

        with stylable_container(key="session_conversation_card", css_styles=CARD_STYLE):
            display_grouped_chat(transcript, epi_summary.get("episodic_summary", {}))
            with stylable_container(key="edit_transcript_scope", css_styles=WHITE_BUTTON_STYLE):
                if st.button("Modifica", key="edit_transcript_btn"):
                    st.session_state["page"] = "edit_session_page"
                    st.session_state["edit_session_id"] = session_id
                    st.info("Pagina di modifica in arrivo!")

        words = transcript.get("data", {}).get("words", [])
        full_text = " ".join(w.get("word", "") for w in words)
        sentences = [s.strip() for s in full_text.split(".") if s.strip()]
        full_transcription = ".\n".join(f"{s}." for s in sentences)

        with stylable_container(key="full_transcription_card", css_styles=CARD_STYLE):
            with st.expander("Trascrizione completa", expanded=True):
                st.write(full_transcription)


def get_transcription_api_call(transcription_id: str) -> Any:
    """Call the API to get session details."""
    try:
        response = requests.get(
            f"{backend_url()}/get_transcription",
            params={"transcription_id": transcription_id},
            headers=auth_headers(),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def get_epi_summary_api_call(trascription_id: str) -> Any:
    """Call the API to get episodic summary."""
    try:
        response = requests.get(
            f"{backend_url()}/get_summary",
            params={"transcription_id": trascription_id},
            headers=auth_headers(),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}
