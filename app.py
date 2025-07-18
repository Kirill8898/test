import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import json
import os
import streamlit_authenticator as stauth

# ---------------------------- CONFIGURATION ----------------------------
# Pre-hashed credentials (generated with stauth.Hasher)
credentials = {
    "usernames": {
        "client1": {
            "name": "Client One",
            "password": "$2b$12$KIXQZtEQo03FnQj6DeZPluFLrGrR/FgxZPMiZPXYu3YyLg17LzAva"  # 'pass123'
        },
        "client2": {
            "name": "Client Two",
            "password": "$2b$12$kKH0iM5zBCxgTRG8tckZ/OFsGVPk6sTnGV/3e0vL3T1BtG7tJX92u"  # 'test456'
        }
    }
}

authenticator = stauth.Authenticate(credentials, "quote_dashboard", "auth_token", cookie_expiry_days=1)
name, auth_status, username = authenticator.login("Login", "main")

if auth_status is False:
    st.error("Invalid username or password")
if auth_status is None:
    st.warning("Please enter your username and password")

# --------------------------- MAIN APP ------------------------------
if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.write(f"👋 Logged in as: {name}")

    # Load persistent storage
    storage_file = f"submissions_{username}.json"
    if os.path.exists(storage_file):
        with open(storage_file, "r") as f:
            st.session_state.submissions = json.load(f)
    else:
        st.session_state.submissions = {}

    st.set_page_config(page_title="Quote Request Dashboard", layout="wide")
    st.title("📋 Medable Quote Request Portal")

    # Helper: Gather prior values
    def get_prior_values(field):
        values = set()
        for entry in st.session_state.submissions.values():
            val = entry.get("General Questions", {}).get(field)
            if val: values.add(val)
        return sorted(list(values))

    menu = st.sidebar.selectbox("Navigation", ["📄 New Request", "📁 My Submissions"])

    if menu == "📄 New Request":
        st.header("Submit a New Quote Request")

        st.subheader("General Scoping Questions")
        sponsor_options = get_prior_values("Sponsor")
        protocol_options = get_prior_values("Sponsor Study/Protocol #")

        general_questions = {
            "Sponsor": st.selectbox("Sponsor", sponsor_options + ["Other"], index=len(sponsor_options)) if sponsor_options else st.text_input("Sponsor"),
            "Sponsor Study/Protocol #": st.selectbox("Sponsor Study/Protocol #", protocol_options + ["Other"], index=len(protocol_options)) if protocol_options else st.text_input("Sponsor Study/Protocol #"),
            "Study Title": st.text_input("Study Title"),
            "Study Phase": st.selectbox("Study Phase", ["", "Phase I", "Phase II", "Phase III", "Phase IV"]),
            "Indication": st.text_input("Indication"),
            "eCOA Device Type": st.selectbox("eCOA Device Type", ["", "BYOD", "Provisioned Device", "Both"]),
            "Estimated First Patient In (FPI)": st.date_input("Estimated FPI")
        }

        if general_questions["Sponsor"] == "Other":
            general_questions["Sponsor"] = st.text_input("Enter new Sponsor")
        if general_questions["Sponsor Study/Protocol #"] == "Other":
            general_questions["Sponsor Study/Protocol #"] = st.text_input("Enter new Protocol #")

        st.subheader("Language-Country-Scope Info")
        langs = st.data_editor(
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
            with open(storage_file, "w") as f:
                json.dump(st.session_state.submissions, f)
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

            if st.download_button("📥 Download All Requests as Excel", pd.json_normalize(list(st.session_state.submissions.values())).to_csv(index=False).encode(), file_name="quote_requests.csv"):
                st.success("📄 File downloaded!")

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
        langs = st.data_editor(
            pd.DataFrame(edit_data["Language Scope"]),
            num_rows="dynamic",
            key="lang_scope_edit"
        )

        st.subheader("Therapeutic Areas")
        selected_areas = st.multiselect("Select Therapeutic Areas", therapeutic_areas, default=edit_data["Therapeutic Areas"])

        if st.button("Save Changes"):
            st.session_state.submissions[edit_id] = {
                "General Questions": general_questions,
                "Language Scope": langs.to_dict(orient="records"),
                "Therapeutic Areas": selected_areas,
                "Submitted At": edit_data["Submitted At"]
            }
            with open(storage_file, "w") as f:
                json.dump(st.session_state.submissions, f)
            del st.session_state.edit_id
            st.success("✅ Changes saved successfully!")
            st.experimental_rerun()
