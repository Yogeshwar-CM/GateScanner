import streamlit as st
import pandas as pd
import os

# ---- CONFIGURATION ----
gate1_file = 'allowed_gate1.xlsx'
gate2_log_file = 'allowed_gate2.xlsx'
id_column = 'REGNO'

# ---- FUNCTIONS ----
def load_gate1_ids():
    if not os.path.exists(gate1_file):
        return set()
    df = pd.read_excel(gate1_file)
    return set(df[id_column].astype(str))

def load_or_create_log(file_name):
    return pd.read_excel(file_name) if os.path.exists(file_name) else pd.DataFrame(columns=[id_column])

def save_log(df, file_name):
    df.to_excel(file_name, index=False)

# ---- STREAMLIT UI ----
st.set_page_config(page_title="Gate 2 Scanner", layout="centered")
st.title("🚧 Gate 2 - Final Checkpoint")

# ---- SESSION STATE INIT ----
if "student_id_gate2" not in st.session_state:
    st.session_state.student_id_gate2 = ""
if "last_status_gate2" not in st.session_state:
    st.session_state.last_status_gate2 = ""
if "last_color_gate2" not in st.session_state:
    st.session_state.last_color_gate2 = "info"

# ---- PROCESSING FUNCTION ----
def process_gate2_scan():
    student_id = st.session_state.student_id_gate2.strip()
    if not student_id:
        return

    gate1_ids = load_gate1_ids()
    gate2_df = load_or_create_log(gate2_log_file)

    if not gate1_ids:
        st.session_state.last_status_gate2 = f"🚫 ERROR: Gate 1 log file not found!"
        st.session_state.last_color_gate2 = "error"
    elif student_id not in gate1_ids:
        st.session_state.last_status_gate2 = f"❌ {student_id} - BLOCKED (Not Cleared at Gate 1)"
        st.session_state.last_color_gate2 = "error"
    elif student_id in gate2_df[id_column].astype(str).values:
        st.session_state.last_status_gate2 = f"⚠️ {student_id} has already entered through Gate 2!"
        st.session_state.last_color_gate2 = "warning"
    else:
        st.session_state.last_status_gate2 = f"✅ {student_id} - FINAL ACCESS GRANTED"
        st.session_state.last_color_gate2 = "success"
        new_entry = pd.DataFrame([{id_column: student_id}])
        gate2_df = pd.concat([gate2_df, new_entry], ignore_index=True)
        save_log(gate2_df, gate2_log_file)

    st.session_state.student_id_gate2 = ""  # Clear the input field

# ---- INPUT FIELD ----
st.text_input(
    "🔍 Scan or Enter REGNO",
    key="student_id_gate2",
    on_change=process_gate2_scan
)

# ---- STATUS FEEDBACK ----
if st.session_state.last_status_gate2:
    match st.session_state.last_color_gate2:
        case "success":
            st.success(st.session_state.last_status_gate2)
        case "warning":
            st.warning(st.session_state.last_status_gate2)
        case "error":
            st.error(st.session_state.last_status_gate2)
        case _:
            st.info(st.session_state.last_status_gate2)

# ---- LOG VIEWER ----
with st.expander("📂 View Gate 2 Logs"):
    if os.path.exists(gate2_log_file):
        st.subheader("✅ Students Entered through Gate 2")
        st.dataframe(pd.read_excel(gate2_log_file))
