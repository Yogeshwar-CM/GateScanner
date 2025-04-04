import streamlit as st
import pandas as pd
import os

# ---- CONFIGURATION ----
detained_files = ['A.xlsx', 'B.xlsx', 'C_corrected.xlsx']
allowed_file = 'allowed_gate1.xlsx'
detained_log_file = 'detained_attempts.xlsx'
id_column = 'REGNO'
override_password = "yarona2025"

# ---- FUNCTIONS ----
def load_detained_ids():
    dfs = [pd.read_excel(f) for f in detained_files if os.path.exists(f)]
    all_detained = pd.concat(dfs)
    return set(all_detained[id_column].astype(str))

def load_or_create_log(file_name):
    return pd.read_excel(file_name) if os.path.exists(file_name) else pd.DataFrame(columns=[id_column])

def save_log(df, file_name):
    df.to_excel(file_name, index=False)

# ---- STREAMLIT UI ----
st.set_page_config(page_title="Gate 1 Scanner", layout="centered")
st.title("🚪 Gate 1 - Entry Scanner")

# Initialize session state
for key, val in {
    "student_id": "",
    "last_status": "",
    "last_color": "info",
    "rejected_id": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Core logic to process a scan
def process_scan():
    student_id = st.session_state.student_id.strip()
    if not student_id:
        return

    detained_ids = load_detained_ids()
    allowed_df = load_or_create_log(allowed_file)
    detained_df = load_or_create_log(detained_log_file)

    # ✅ Check valid year prefixes
    if not student_id.startswith(("21", "22", "23", "24")):
        st.session_state.last_status = f"❌ {student_id} - PASSED / (Invalid Year)"
        st.session_state.last_color = "error"
        st.session_state.rejected_id = student_id
        st.session_state.student_id = ""
        return

    # ✅ Priority: Detained check
    if student_id in detained_ids:
        st.session_state.last_status = f"❌ {student_id} - ACCESS DENIED (Detained)"
        st.session_state.last_color = "error"
        st.session_state.rejected_id = student_id
        if student_id not in detained_df[id_column].astype(str).values:
            new_entry = pd.DataFrame([{id_column: student_id}])
            detained_df = pd.concat([detained_df, new_entry], ignore_index=True)
            save_log(detained_df, detained_log_file)
        st.session_state.student_id = ""
        return

    # ⚠️ Already scanned (non-detained)
    if student_id in allowed_df[id_column].astype(str).values:
        st.session_state.last_status = f"⚠️ {student_id} has already been scanned!"
        st.session_state.last_color = "warning"
        st.session_state.student_id = ""
        return

    # ✅ New allowed entry
    st.session_state.last_status = f"✅ {student_id} - ACCESS GRANTED (Welcome)"
    st.session_state.last_color = "success"
    st.session_state.rejected_id = ""
    new_entry = pd.DataFrame([{id_column: student_id}])
    allowed_df = pd.concat([allowed_df, new_entry], ignore_index=True)
    save_log(allowed_df, allowed_file)
    st.session_state.student_id = ""

# Input field with live clearing
st.text_input(
    "🔍 Scan or Enter REGNO",
    key="student_id",
    on_change=process_scan
)

# Feedback Message (sticky)
if st.session_state.last_status:
    match st.session_state.last_color:
        case "success":
            st.success(st.session_state.last_status)
        case "warning":
            st.warning(st.session_state.last_status)
        case "error":
            st.error(st.session_state.last_status)
        case _:
            st.info(st.session_state.last_status)

# 🔓 Allow Anyway Override
if (
    st.session_state.last_color == "error"
    and st.session_state.rejected_id
):
    with st.expander("🔓 Override Access with Password"):
        password = st.text_input("Enter override password", type="password", key="override_pw")
        if st.button("Allow Anyway"):
            if password == override_password:
                allowed_df = load_or_create_log(allowed_file)
                student_id = st.session_state.rejected_id
                new_entry = pd.DataFrame([{id_column: student_id}])
                allowed_df = pd.concat([allowed_df, new_entry], ignore_index=True)
                save_log(allowed_df, allowed_file)
                st.session_state.last_status = f"✅ {student_id} - ACCESS GRANTED (Manually Overridden)"
                st.session_state.last_color = "success"
                st.session_state.rejected_id = ""
            else:
                st.error("Incorrect password.")

# View logs
with st.expander("📂 View Current Logs"):
    if os.path.exists(allowed_file):
        st.subheader("✅ Allowed Entries")
        st.dataframe(pd.read_excel(allowed_file))
    if os.path.exists(detained_log_file):
        st.subheader("❌ Detained Attempts")
        st.dataframe(pd.read_excel(detained_log_file))