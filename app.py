import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

# Initialize session state for submissions
if "submissions" not in st.session_state:
    st.session_state.submissions = {}

st.set_page_config(page_title="Quote Request Dashboard", layout="wide")
st.title("📋 Medable Quote Request Portal")

menu = st.sidebar.selectbox("Navigation", ["📄 New Request", "📁 My Submissions"])

if menu == "📄 New Request":
    st.header("Submit a New Quote Request")

    st.subheader("General Scoping Questions")
    general_questions = {
        "Sponsor": st.text_input("Sponsor"),
        "Sponsor Study/Protocol #": st.text_input("Sponsor Study/Protocol #"),
        "Study Title": st.text_input("Study Title"),
        "Study Phase": st.selectbox("Study Phase", ["", "Phase I", "Phase II", "Phase III", "Phase IV"]),
        "Indication": st.text_input("Indication"),
        "eCOA Device Type": st.selectbox("eCOA Device Type", ["", "BYOD", "Provisioned Device", "Both"]),
        "Estimated First Patient In (FPI)": st.date_input("Estimated FPI")
    }

    st.subheader("Language-Country-Scope Info")
    langs = st.experimental_data_editor(
        pd.DataFrame(columns=["Country", "Language", "Batch", "Requested Deadline"]),
        num_rows="dynamic",
        key="lang_scope_new"
    )

    st.subheader("Therapeutic Areas")
    therapeutic_areas = [
        "Addiction", "Allergy", "Analgesia/Anesthesiology/Anti-inflammatory", "Autoimmune",
        "Cardiology/Cardiovascular", "Dermatology"
    ]
    selected_areas = st.multiselect("Select Therapeutic Areas", therapeutic_areas)

    if st.button("Submit Request"):
        submission_id = str(uuid.uuid4())
        st.session_state.submissions[submission_id] = {
            "General Questions": general_questions,
            "Language Scope": langs.to_dict(orient="records"),
            "Therapeutic Areas": selected_areas,
            "Submitted At": datetime.now().isoformat()
        }
        st.success("✅ Request submitted successfully!")
        st.balloons()

elif menu == "📁 My Submissions":
    st.header("Your Submitted Requests")

    if not st.session_state.submissions:
        st.info("You haven’t submitted any requests yet.")
    else:
        for sub_id, data in st.session_state.submissions.items():
            with st.expander(f"Request ID: {sub_id}"):
                st.write("Submitted At:", data["Submitted At"])
                st.write("General Questions")
                st.json(data["General Questions"])
                st.write("Language Scope")
                st.dataframe(pd.DataFrame(data["Language Scope"]))
                st.write("Therapeutic Areas")
                st.write(", ".join(data["Therapeutic Areas"]))

                if st.button(f"Edit Request", key=f"edit_{sub_id}"):
                    st.session_state.edit_id = sub_id
                    st.experimental_rerun()

# Handle editing
if "edit_id" in st.session_state:
    edit_id = st.session_state.edit_id
    edit_data = st.session_state.submissions[edit_id]

    st.sidebar.markdown("---")
    st.sidebar.subheader("🛠 Editing Request")
    st.sidebar.write(f"Request ID: {edit_id}")

    st.header("✏️ Edit Your Quote Request")
    st.subheader("General Scoping Questions")
    general_questions = {}
    for k, v in edit_data["General Questions"].items():
        general_questions[k] = st.text_input(k, value=v)

    st.subheader("Language-Country-Scope Info")
    langs = st.experimental_data_editor(
        pd.DataFrame(edit_data["Language Scope"]),
        num_rows="dynamic",
        key="lang_scope_edit"
    )

    st.subheader("Therapeutic Areas")
    therapeutic_areas = [
        "Addiction", "Allergy", "Analgesia/Anesthesiology/Anti-inflammatory", "Autoimmune",
        "Cardiology/Cardiovascular", "Dermatology"
    ]
    selected_areas = st.multiselect("Select Therapeutic Areas", therapeutic_areas, default=edit_data["Therapeutic Areas"])

    if st.button("Save Changes"):
        st.session_state.submissions[edit_id] = {
            "General Questions": general_questions,
            "Language Scope": langs.to_dict(orient="records"),
            "Therapeutic Areas": selected_areas,
            "Submitted At": edit_data["Submitted At"]
        }
        del st.session_state.edit_id
        st.success("✅ Changes saved successfully!")
        st.experimental_rerun()
