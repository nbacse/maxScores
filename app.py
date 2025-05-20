import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Question-wise Max Scores Per USN")

uploadedFile = st.file_uploader("Upload Excel file", type=["xls", "xlsx"])

if uploadedFile is not None:
    try:
        # Handle both .xls and .xlsx
        if uploadedFile.name.endswith(".xls"):
            df = pd.read_excel(uploadedFile, engine="xlrd", header=None)
        else:
            df = pd.read_excel(uploadedFile, header=None)

        # Detect USN row and column
        usnPattern = re.compile(r"\b1(?:[A-Z]{2})?(?:\d{2})?[A-Z]{2}\d{3}\b", re.IGNORECASE)

        usnRowIndex, usnColIndex = None, None
        for rowIdx in range(len(df)):
            for colIdx in range(df.shape[1]):
                cellValue = str(df.iat[rowIdx, colIdx])
                if usnPattern.search(cellValue):
                    usnRowIndex, usnColIndex = rowIdx, colIdx
                    break
            if usnRowIndex is not None:
                break

        if usnRowIndex is None:
            st.error("USN column not found based on pattern (e.g., 1BY22CS001). Please check your file.")
        else:
            # Extract header and data
            headers = df.iloc[usnRowIndex - 1].tolist()
            data = df.iloc[usnRowIndex:].copy()
            data.columns = headers
            data.reset_index(drop=True, inplace=True)

            usnColName = headers[usnColIndex]
            grouped = {}

            for _, row in data.iterrows():
                usn = row[usnColName]
                if pd.isna(usn):
                    continue
                if usn not in grouped:
                    grouped[usn] = []
                grouped[usn].append(row)

            maxScoreRows = []
            for usn, rows in grouped.items():
                scoresDf = pd.DataFrame(rows)
                maxRow = {usnColName: usn}
                for col in scoresDf.columns:
                    if col == usnColName:
                        continue
                    try:
                        numericVals = pd.to_numeric(scoresDf[col], errors='coerce')
                        maxVal = numericVals.max()
                        if pd.notna(maxVal):
                            maxRow[col] = maxVal
                    except:
                        continue
                maxScoreRows.append(maxRow)

            outputDf = pd.DataFrame(maxScoreRows)

            # Remove columns B and C (i.e., 2nd and 3rd columns) if they exist
            if outputDf.shape[1] > 2:
                outputDf.drop(outputDf.columns[[1, 2]], axis=1, inplace=True)

            # Download link
            towrite = BytesIO()
            originalName = uploadedFile.name.rsplit(".", 1)[0]
            outputDf.to_excel(towrite, index=False, sheet_name="Max Scores")
            towrite.seek(0)

            st.success("✅ Max scores computed successfully.")
            st.download_button(
                label="📥 Download MaxScores Excel File",
                data=towrite,
                file_name=f"maxscores_{originalName}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
