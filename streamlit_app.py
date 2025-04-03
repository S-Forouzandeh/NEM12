# streamlit_app.py
import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Standard NEM12 row types
ROW_ORDER = ["100", "200", "300", "400", "900"]

# Templates for missing row types
ROW_TEMPLATES = {
    "100": ["100", "NEM12", datetime.now().strftime("%Y%m%d%H%M"), "MDP", "ParticipantID"],
    "200": ["200", "NMI", "RegisterID", "NMISuffix", "MDM_DataStream", "UOM", "Interval", "NextScheduledRead"],
    "300": ["300", "Date", "Quality_Method", "Reason_Code", "Reason_Description"],
    "400": ["400", "StartInterval", "EndInterval", "Quality_Method", "Reason_Code"],
    "900": ["900"]
}

def extract_nem12_data(df, file_name):
    """Extract and categorize rows based on NEM12 row types."""
    df = df.dropna(how="all")  # Drop fully empty rows
    
    # Initialize dictionary to hold all possible row types
    nem12_data = {key: [] for key in ROW_ORDER}
    
    # Check if the first column contains row type indicators
    has_row_indicators = False
    
    # Identify row types in the first column
    if not df.empty and df.shape[1] > 0:
        first_col = df.iloc[:, 0].astype(str).str.strip()
        nem12_row_types = first_col[first_col.isin(ROW_ORDER)]
        
        if not nem12_row_types.empty:
            has_row_indicators = True
            
            # Extract rows by NEM12 type
            for _, row in df.iterrows():
                row_type = str(row.iloc[0]).strip()
                if row_type in ROW_ORDER:
                    nem12_data[row_type].append(row.tolist())
        else:
            # Try to infer structure if no standard row indicators
            st.info(f"No standard NEM12 row indicators found in {file_name}. Attempting to infer structure.")
            
            # Simple inference: if the file has data, treat it as 300 row type (readings)
            if df.shape[0] > 1:
                # Check if this looks like interval data (many rows)
                if df.shape[0] > 10:
                    nem12_data["300"] = df.values.tolist()
                else:
                    # Otherwise, use the first row as header (200) and the rest as data (300)
                    nem12_data["200"] = [df.iloc[0].tolist()]
                    nem12_data["300"] = df.iloc[1:].values.tolist()
    
    # Check if we found any valid data
    any_data_found = any(len(rows) > 0 for rows in nem12_data.values())
    
    if not any_data_found:
        st.warning(f"No valid NEM12 data could be extracted from {file_name}")
        return None
    
    return {
        "file": file_name,
        "structured_data": nem12_data,
        "has_standard_format": has_row_indicators
    }

def process_uploaded_file(file):
    """Process uploaded file and extract NEM12 data."""
    filename = file.name
    results = []
    
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(file, header=None, encoding="ISO-8859-1", dtype=str, on_bad_lines="skip")
            data = extract_nem12_data(df, filename)
            if data:
                results.append(data)
                
        elif filename.endswith((".xlsx", ".xls")):
            xls = pd.ExcelFile(file)
            
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet, header=None, dtype=str)
                if not df.empty:
                    data = extract_nem12_data(df, f"{filename} (Sheet: {sheet})")
                    if data:
                        results.append(data)
    except Exception as e:
        st.error(f"Error processing file {filename}: {str(e)}")
        logger.error(f"Error processing file {filename}: {e}", exc_info=True)
    
    return results

def generate_nem12_file(processed_data):
    """Generate a valid NEM12-format file with appropriate row structure."""
    if not processed_data:
        st.error("No valid data to generate NEM12 file")
        return None
    
    all_blocks = []
    file_info = []

    for data in processed_data:
        nem12_rows = []
        structured_data = data["structured_data"]
        file_info.append(data["file"])
        
        # Process each row type in order
        for row_type in ROW_ORDER:
            rows = structured_data.get(row_type, [])
            
            # If this row type is missing, add template (except for 900 which we'll add at the end)
            if not rows and row_type != "900":
                # Only add required rows: 100 is always required, 200 is required if we have 300s
                if row_type == "100" or (row_type == "200" and structured_data.get("300", [])):
                    st.info(f"Adding template {row_type} row for {data['file']}")
                    rows = [ROW_TEMPLATES[row_type]]
            
            nem12_rows.extend(rows)
        
        # Ensure each segment ends with 900
        if not any(row[0] == "900" for row in nem12_rows):
            nem12_rows.append(ROW_TEMPLATES["900"])
        
        # Ensure each segment starts with 100
        if not any(row[0] == "100" for row in nem12_rows):
            nem12_rows.insert(0, ROW_TEMPLATES["100"])
        
        # Sort rows by NEM12 row type within each block
        if nem12_rows:
            nem12_df = pd.DataFrame(nem12_rows)
            nem12_df.iloc[:, 0] = nem12_df.iloc[:, 0].astype(str)
            
            # Create a sort key map
            sort_map = {k: i for i, k in enumerate(ROW_ORDER)}
            
            # Apply sorting
            try:
                nem12_df.sort_values(
                    by=nem12_df.columns[0], 
                    key=lambda x: x.map(sort_map), 
                    inplace=True
                )
            except Exception as e:
                st.error(f"Error sorting rows: {str(e)}")
                
            all_blocks.append(nem12_df)

    if all_blocks:
        # Combine all blocks
        final_df = pd.concat(all_blocks, ignore_index=True)
        final_df.dropna(axis=1, how="all", inplace=True)
        
        # Save to string buffer
        output = StringIO()
        final_df.to_csv(output, index=False, header=False)
        return output.getvalue(), file_info
    else:
        st.error("No valid blocks to write to output file")
        return None, []

# Streamlit UI
st.title("🔌 NEM12 Generator")
st.markdown("""
This app processes files into standard NEM12 format. It can handle:
- Files with standard NEM12 row types (100, 200, 300, 400, 900)
- Files missing some or all standard row types
- Various data formats by auto-inferring structure
""")

uploaded_files = st.file_uploader("Upload CSV or Excel files", type=["csv", "xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("Processing files..."):
        all_data = []
        for file in uploaded_files:
            file_data = process_uploaded_file(file)
            all_data.extend(file_data)
        
        if all_data:
            result_csv, processed_files = generate_nem12_file(all_data)
            
            if result_csv:
                st.success(f"✅ NEM12 File Generated from {len(processed_files)} data sources!")
                
                # Show which files were processed
                with st.expander("Show processed data sources"):
                    for file in processed_files:
                        st.text(f"- {file}")
                
                # Preview
                with st.expander("Preview NEM12 Output"):
                    preview_lines = result_csv.split('\n')[:50]  # Show first 50 lines
                    st.code('\n'.join(preview_lines) + ('\n...' if len(preview_lines) >= 50 else ''), language="csv")
                
                # Download button
                st.download_button(
                    "📥 Download NEM12 File", 
                    result_csv, 
                    file_name=f"NEM12_Output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.error("No valid NEM12 data could be extracted from the uploaded files.")
