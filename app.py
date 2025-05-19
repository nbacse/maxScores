import streamlit as st
import pandas as pd
import io
import re

st.title("🎓 Max Scores Per USN")

uploadedFile = st.file_uploader("📤 Upload your Excel file", type=["xlsx"])

def detect_usn_column(df):
    usn_pattern = re.compile(r"1BY21", re.IGNORECASE)
    for col in df.columns[:2]:  # Only check first two columns (A or B)
        if df[col].astype(str).str.contains(usn_pattern).any():
            return col
    return None

if uploadedFile:
    df = pd.read_excel(uploadedFile)

    usn_col = detect_usn_column(df)

    if not usn_col:
        st.error("❌ USN column not found. Ensure a column contains '1BY21' pattern.")
    else:
        st.success(f"✅ Detected USN column: {usn_col}")
        st.write("### 📋 Uploaded Data Preview", df.head())

        grouped = df.groupby(usn_col)

        output = df.iloc[0:0].copy()  # Empty DataFrame with same headers

        for usn, group in grouped:
            maxRow = [usn]
            for col in df.columns:
                if col == usn_col:
                    continue
                colValues = pd.to_numeric(group[col], errors='coerce')
                maxRow.append(colValues.max(skipna=True))
            rowDict = dict(zip([usn_col] + [c for c in df.columns if c != usn_col], maxRow))
            output = output.append(rowDict, ignore_index=True)

        # Reorder columns
        output = output[[usn_col] + [c for c in df.columns if c != usn_col]]

        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
            output.to_excel(writer, index=False, sheet_name="Max Scores")

        st.download_button(
            label="📥 Download Max Scores Excel",
            data=towrite.getvalue(),
            file_name="max_scores_per_usn.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
