# streamlit_app.py

import streamlit as st
import pandas as pd
from io import StringIO

ROW_ORDER = ["100", "200", "300", "400", "900"]

def extract_nem12_data(df):
    df = df.dropna(how="all")
    nem12_data = {key: [] for key in ROW_ORDER}
    for _, row in df.iterrows():
        row_type = str(row.iloc[0]).strip()
        if row_type in nem12_data:
            nem12_data[row_type].append(row.tolist())
    return nem12_data

def process_uploaded_file(file):
    filename = file.name
    if filename.endswith(".csv"):
        df = pd.read_csv(file, header=None, encoding="ISO-8859-1", dtype=str, on_bad_lines="skip")
        return [{"file": filename, "structured_data": extract_nem12_data(df)}]
    elif filename.endswith(".xlsx"):
        results = []
        xls = pd.ExcelFile(file)
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, header=None, dtype=str)
            if not df.empty:
                results.append({"file": f"{filename}::{sheet}", "structured_data": extract_nem12_data(df)})
        return results
    return []

def generate_nem12_file(processed_data):
    all_blocks = []
    for data in processed_data:
        nem12_rows = []
        for row_type in ROW_ORDER[:-1]:
            rows = data["structured_data"].get(row_type, [])
            nem12_rows.extend(rows)

        if not any(row[0] == "100" for row in nem12_rows):
            nem12_rows.insert(0, ["100", "NEM12", "YYYYMMDDHHMM", "MDP", "ParticipantID"])
        nem12_rows.append(["900"])

        df = pd.DataFrame(nem12_rows)
        df.iloc[:, 0] = df.iloc[:, 0].astype(str)
        df.sort_values(by=df.columns[0], key=lambda x: x.map({k: i for i, k in enumerate(ROW_ORDER)}), inplace=True)
        all_blocks.append(df)

    final_df = pd.concat(all_blocks, ignore_index=True)
    final_df.dropna(axis=1, how="all", inplace=True)
    output = StringIO()
    final_df.to_csv(output, index=False, header=False)
    return output.getvalue()

# Streamlit UI
st.title("🔌 NEM12 Generator")
uploaded_files = st.file_uploader("Upload CSV or Excel files", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        all_data.extend(process_uploaded_file(file))

    if all_data:
        result_csv = generate_nem12_file(all_data)
        st.success("✅ NEM12 File Generated!")
        st.download_button("📥 Download NEM12 File", result_csv, file_name="Final_NEM12_Output.csv", mime="text/csv")