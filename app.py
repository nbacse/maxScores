import streamlit as st
import pandas as pd
import io
import re

st.title("Question-wise Max Scores Per USN")

def find_header_and_usn_col(df):
    # Scan first 10 rows, columns A(0) and B(1) to find USN pattern '1BY', '1TD', '1TE', '1BY21', '1BY22', etc.
    usn_pattern = re.compile(r"1(b[ytd]|BY21|BY22|BY23|TD|TE)", re.I)
    for i in range(min(10, len(df))):
        for col in [0, 1]:
            cell_val = str(df.iat[i, col]).strip()
            if usn_pattern.match(cell_val):
                return i, col
    # Default fallback
    return 0, 0

uploadedFile = st.file_uploader("Upload Excel file (xlsx)", type=["xlsx"])

if uploadedFile is not None:
    try:
        # Read entire file without header to locate header row dynamically
        df_raw = pd.read_excel(uploadedFile, header=None)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    header_row_idx, usn_col_idx = find_header_and_usn_col(df_raw)

    # Re-read with proper header row
    uploadedFile.seek(0)
    df = pd.read_excel(uploadedFile, header=header_row_idx)
    headers = list(df.columns)

    # Filter rows below header
    df_data = df.iloc[(header_row_idx + 1) - header_row_idx :].reset_index(drop=True)

    # Filter rows that have a valid USN pattern in detected USN column
    usn_pattern = re.compile(r"1(b[ytd]|BY\d{2}|TD|TE)", re.I)
    df_data = df_data[df[headers[usn_col_idx]].astype(str).str.match(usn_pattern)]

    if df_data.empty:
        st.error("No valid USN data found based on detected pattern. Please check your file.")
        st.stop()

    st.subheader("Preview of Uploaded Data (Top 5 rows)")
    st.dataframe(df.head(5))

    # Group by USN
    usnMap = {}
    for _, row in df_data.iterrows():
        usn = str(row[headers[usn_col_idx]]).strip()
        if usn not in usnMap:
            usnMap[usn] = []
        usnMap[usn].append(row)

    # Identify start of score columns: after USN col (start from usn_col_idx+1)
    startScoreCol = usn_col_idx + 1

    resultRows = []
    for usn, rows in usnMap.items():
        firstRow = rows[0].copy()
        for colIndex in range(startScoreCol, len(headers)):
            colScores = []
            for r in rows:
                val = r[headers[colIndex]]
                try:
                    score = float(val)
                    colScores.append(score)
                except (ValueError, TypeError):
                    pass
            maxScore = max(colScores) if colScores else 0
            firstRow[headers[colIndex]] = maxScore
        resultRows.append(firstRow)

    outputDf = pd.DataFrame(resultRows, columns=headers)

    st.success("Max scores computed successfully!")

    # Download button
    originalName = uploadedFile.name.rsplit(".", 1)[0]
    outputFilename = f"maxscores_{originalName}.xlsx"

    towrite = io.BytesIO()
    outputDf.to_excel(towrite, index=False)
    towrite.seek(0)

    st.download_button(
        label="📥 Download MaxScores Excel File",
        data=towrite,
        file_name=outputFilename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
