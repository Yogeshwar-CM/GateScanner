import streamlit as st
import pandas as pd
import os

# ---- CONFIGURATION ----
detained_files = ['A.xlsx', 'B.xlsx', 'C_corrected.xlsx']
allowed_file = 'allowed_gate1.xlsx'
detained_log_file = 'detained_attempts.xlsx'
id_column = 'REGNO'

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
if "student_id" not in st.session_state:
    st.session_state.student_id = ""
if "last_status" not in st.session_state:
    st.session_state.last_status = ""
if "last_color" not in st.session_state:
    st.session_state.last_color = "info"

# Core logic to process a scan
def process_scan():
    student_id = st.session_state.student_id.strip()
    if not student_id:

        return

    # ✅ Check valid year prefixes
    if not student_id.startswith(("21", "22", "23", "24")):
        st.session_state.last_status = f"❌ {student_id} - PASSED / (Invalid Year)"
        st.session_state.last_color = "error"
        st.session_state.student_id = ""
        return

    detained_ids = load_detained_ids()
    allowed_df = load_or_create_log(allowed_file)
    detained_df = load_or_create_log(detained_log_file)

    # ✅ Priority: Detained check
    if student_id in detained_ids:
        st.session_state.last_status = f"❌ {student_id} - ACCESS DENIED (Detained)"
        st.session_state.last_color = "error"
        if student_id not in detained_df[id_column].astype(str).values:
            new_entry = pd.DataFrame([{id_column: student_id}])
            detained_df = pd.concat([detained_df, new_entry], ignore_index=True)
            save_log(detained_df, detained_log_file)

    # ⚠️ Already scanned (non-detained)
    elif student_id in allowed_df[id_column].astype(str).values:
        st.session_state.last_status = f"⚠️ {student_id} has already been scanned!"
        st.session_state.last_color = "warning"

    # ✅ New allowed entry
    else:
        st.session_state.last_status = f"✅ {student_id} - ACCESS GRANTED (Welcome)"
        st.session_state.last_color = "success"
        new_entry = pd.DataFrame([{id_column: student_id}])
        allowed_df = pd.concat([allowed_df, new_entry], ignore_index=True)
        save_log(allowed_df, allowed_file)

    # Clear the input field only
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

# View logs below
with st.expander("📂 View Current Logs"):
    if os.path.exists(allowed_file):
        st.subheader("✅ Allowed Entries")
        st.dataframe(pd.read_excel(allowed_file))
    if os.path.exists(detained_log_file):
        st.subheader("❌ Detained Attempts")
        st.dataframe(pd.read_excel(detained_log_file))
