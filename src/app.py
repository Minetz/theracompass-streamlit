"""Streamlit user app."""

import streamlit as st

from account_page import account_page
from home_page import home_page
from login import login
from patient_page import patient_page
from session_page import session_page

# User app design

# An authentication layer (sign in with google)
# Once authenticated:
# Create Patient file.
# Each Patient can have multiple independant recordings.


# Run the app
st.set_page_config(page_title="TheraCompass", layout="wide")
st.session_state.setdefault("page", "home_page")

if __name__ == "__main__":
    # Check if user is logged in
    if st.session_state.get("user_id") is None:
        login(user_id=st.session_state.get("user_id", ""))
    # If user is logged in, show the home page or patient page
    elif st.session_state["page"] == "home_page":
        home_page()
    # If user clicks on a patient, show the patient page
    elif st.session_state["page"] == "patient_page":
        # Check if a patient ID is selected
        if st.session_state["selected_patient_id"]:
            # Render the patient page with the selected patient ID
            patient_page(st.session_state["selected_patient_id"])
        else:
            st.error("Nessun paziente selezionato.")
    elif st.session_state["page"] == "session_page":
        session_page(st.session_state["selected_session_id"])
    elif st.session_state["page"] == "account_page":
        account_page()
    else:
        st.error("Stato pagina sconosciuto.")
        st.write("ATTENZIONE: ritorno alla home page")
        home_page()
