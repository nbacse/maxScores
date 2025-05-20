import streamlit as st
import pandas as pd
import io
import re

st.title("Question-wise Max Scores Per USN")

def find_usn_column_and_header(df):
    usn_pattern = re.compile(r"1(by|te|td)\d*", re.I)
    for row_idx in range(len(df)):
        for col_idx in range(len(df.columns)):
            cell_value = str(df.iat[row_idx, col_idx]).strip()
            if usn_pattern.match(cell_value):
                header_row = row_idx - 1 if row_idx > 0 else 0
                usn_col = col_idx
                return usn_col, header_row
    # If no USN pattern found, fallback to first column and header row 0
    return 0, 0

def main():
    uploadedFile = st.file_uploader(
        "Upload Excel file (xls or xlsx)",
        type=["xls", "xlsx"]
    )
    if uploadedFile is not None:
        # Read file without header, to detect USN and header row
        try:
            raw_df = pd.read_excel(uploadedFile, header=None)
        except Exception as e:
            st.error(f"Error reading the file: {e}")
            return
        
        usn_col, header_row = find_usn_column_and_header(raw_df)

        # Read again with correct header row
        uploadedFile.seek(0)  # reset file pointer
        try:
            df = pd.read_excel(uploadedFile, header=header_row)
        except Exception as e:
            st.error(f"Error reading the file with header row {header_row+1}: {e}")
            return
        
        # Show detected info
        st.write(f"Detected USN column: **{df.columns[usn_col]}** (index {usn_col})")
        st.write(f"Detected header row: **{header_row + 1}**")

        st.subheader("Preview of uploaded data (top 5 rows):")
        st.dataframe(df.head(5))

        # Group rows by USN
        usn_pattern = re.compile(r"1(by|te|td)\d*", re.I)
        usnMap = {}
        for idx, row in df.iterrows():
            usn = str(row.iloc[usn_col]).strip()
            if not usn or not usn_pattern.match(usn):
                continue
            if usn not in usnMap:
                usnMap[usn] = []
            usnMap[usn].append(row)

        # Prepare result rows: headers + max scores per USN
        headers = list(df.columns)
        result = [headers]

        for usn, rows in usnMap.items():
            # Convert list of Series to DataFrame
            usn_df = pd.DataFrame(rows)

            # First column is USN column, keep as is
            # For rest columns, compute max if numeric else keep first occurrence
            max_row = []
            for i, col in enumerate(headers):
                if i == usn_col:
                    max_row.append(usn)
                else:
                    # Attempt numeric max if possible, else first non-null value
                    col_values = pd.to_numeric(usn_df[col], errors='coerce')
                    if col_values.notna().any():
                        max_val = col_values.max()
                        max_row.append(max_val)
                    else:
                        # fallback to first non-null or empty string
                        non_null_vals = usn_df[col].dropna()
                        max_row.append(non_null_vals.iloc[0] if not non_null_vals.empty else "")

            result.append(max_row)

        # Convert result to DataFrame for output
        output_df = pd.DataFrame(result[1:], columns=result[0])

        st.success("Max scores computed successfully!")

        # Prepare Excel for download
        output_buffer = io.BytesIO()
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            output_df.to_excel(writer, index=False, sheet_name="Max Scores")

        output_buffer.seek(0)

        original_name = uploadedFile.name if uploadedFile.name else "uploadedfile.xlsx"
        filename_out = f"maxscores_{original_name}"
        
        st.download_button(
            label="📥 Download MaxScores Excel File",
            data=output_buffer,
            file_name=filename_out,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
