import streamlit as st
import pandas as pd
import os

# ---- CONFIGURATION ----
detained_files = ['A.xlsx', 'B.xlsx', 'C_corrected.xlsx']
log_file = 'DATA.csv'
detained_log_file = 'detained_attempts.xlsx'
gate2_log_file = 'allowed_gate2.xlsx'
id_column = 'REGNO'
override_password = "yarona2025"

# ---- FUNCTIONS ----
def load_detained_ids():
    dfs = [pd.read_excel(f) for f in detained_files if os.path.exists(f)]
    all_detained = pd.concat(dfs)
    return set(all_detained[id_column].astype(str))

def load_or_create_log(file_name):
    if not os.path.exists(file_name):
        return pd.DataFrame(columns=[id_column])
    if file_name.endswith('.csv'):
        return pd.read_csv(file_name)
    return pd.read_excel(file_name)

def save_log(df, file_name):
    if file_name.endswith('.csv'):
        df.to_csv(file_name, index=False)
    else:
        df.to_excel(file_name, index=False)

def gate1_process(student_id):
    detained_ids = load_detained_ids()
    allowed_df = load_or_create_log(log_file)
    detained_df = load_or_create_log(detained_log_file)

    if not student_id.startswith(("21", "22", "23", "24")):
        return "❌ {} - PASSED / (Invalid Year)".format(student_id), "error"

    if student_id in detained_ids:
        if student_id not in detained_df[id_column].astype(str).values:
            new_entry = pd.DataFrame([{id_column: student_id}])
            detained_df = pd.concat([detained_df, new_entry], ignore_index=True)
            save_log(detained_df, detained_log_file)
        return "❌ {} - ACCESS DENIED (Detained)".format(student_id), "error"

    if student_id in allowed_df[id_column].astype(str).values:
        return "⚠️ {} has already been scanned!".format(student_id), "warning"

    new_entry = pd.DataFrame([{id_column: student_id}])
    allowed_df = pd.concat([allowed_df, new_entry], ignore_index=True)
    save_log(allowed_df, log_file)
    return "✅ {} - ACCESS GRANTED (Welcome)".format(student_id), "success"

def gate2_process(student_id):
    allowed_df = load_or_create_log(log_file)
    gate2_df = load_or_create_log(gate2_log_file)

    if student_id not in allowed_df[id_column].astype(str).values:
        return "❌ {} - BLOCKED (Not Cleared at Gate 1)".format(student_id), "error"

    if student_id in gate2_df[id_column].astype(str).values:
        return "⚠️ {} has already entered through Gate 2!".format(student_id), "warning"

    new_entry = pd.DataFrame([{id_column: student_id}])
    gate2_df = pd.concat([gate2_df, new_entry], ignore_index=True)
    save_log(gate2_df, gate2_log_file)
    return "✅ {} - FINAL ACCESS GRANTED".format(student_id), "success"

# ---- STREAMLIT UI ----
st.set_page_config(page_title="Gate Scanner", layout="centered")
st.title("🎫 Multi-Gate Entry Scanner")

gate = st.radio("Select Gate", ["Gate 1", "Gate 2"])

if gate == "Gate 1":
    st.header("🚪 Gate 1 - Entry Scanner")
    student_id = st.text_input("🔍 Scan or Enter REGNO", key="gate1_input")

    if student_id:
        status, color = gate1_process(student_id.strip())
        match color:
            case "success": st.success(status)
            case "warning": st.warning(status)
            case "error": st.error(status)
            case _: st.info(status)

        # Override option
        if "ACCESS DENIED" in status:
            with st.expander("🔓 Override Access with Password"):
                password = st.text_input("Enter override password", type="password")
                if st.button("Allow Anyway"):
                    if password == override_password:
                        allowed_df = load_or_create_log(log_file)
                        new_entry = pd.DataFrame([{id_column: student_id}])
                        allowed_df = pd.concat([allowed_df, new_entry], ignore_index=True)
                        save_log(allowed_df, log_file)
                        st.success(f"✅ {student_id} - ACCESS GRANTED (Manually Overridden)")
                    else:
                        st.error("Incorrect password.")

    with st.expander("📂 View Logs"):
        if os.path.exists(log_file):
            st.subheader("✅ Allowed Entries")
            st.dataframe(load_or_create_log(log_file))
        if os.path.exists(detained_log_file):
            st.subheader("❌ Detained Attempts")
            st.dataframe(load_or_create_log(detained_log_file))

else:
    st.header("🚧 Gate 2 - Final Checkpoint")
    student_id_gate2 = st.text_input("🔍 Scan or Enter REGNO", key="gate2_input")

    if student_id_gate2:
        status, color = gate2_process(student_id_gate2.strip())
        match color:
            case "success": st.success(status)
            case "warning": st.warning(status)
            case "error": st.error(status)
            case _: st.info(status)

    with st.expander("📂 View Gate 2 Logs"):
        if os.path.exists(gate2_log_file):
            st.subheader("✅ Students Entered through Gate 2")
            st.dataframe(load_or_create_log(gate2_log_file))