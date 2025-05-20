import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Question-wise Max Scores Per USN")

uploadedFile = st.file_uploader("Upload Excel file (.xls or .xlsx)", type=["xls", "xlsx"])

def make_unique(cols):
    seen = {}
    newCols = []
    for col in cols:
        if col in seen:
            seen[col] += 1
            newCols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            newCols.append(col)
    return newCols

if uploadedFile is not None:
    # Read Excel
    try:
        df = pd.read_excel(uploadedFile, header=None)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # Detect USN row and column
    usnRowIndex = None
    usnColIndex = None
    usnPattern = re.compile(r"1(?:by|td|te)[\d]{0,2}", re.IGNORECASE)  # pattern covers your cases

    for i, row in df.iterrows():
        for j, cell in enumerate(row):
            if isinstance(cell, str) and usnPattern.match(cell.strip()):
                usnRowIndex = i
                usnColIndex = j
                break
        if usnRowIndex is not None:
            break

    if usnRowIndex is None:
        st.error("❌ Could not find USN pattern like '1BY22', '1TD', '1TE', etc.")
        st.stop()

    if usnRowIndex == 0:
        st.error("USN found in first row; cannot identify header row above it.")
        st.stop()

    headerRowIndex = usnRowIndex - 1

    headers = df.iloc[headerRowIndex].astype(str).tolist()
    headers = make_unique(headers)

    data = df.iloc[usnRowIndex:].copy()
    data.columns = headers
    data.reset_index(drop=True, inplace=True)

    st.subheader("Preview of Input Data (top 5 rows)")
    st.dataframe(data.head(5))

    # Prepare for max score calc
    # USN col is usnColIndex (e.g. 0 or 1)
    # Scores start from col 3 (D) per your original Google Apps Script,
    # but here we keep it flexible: max scores from columns to right of USN col + 2
    # We'll assume scores start from column index 3 onwards (like original) or after USN col + 2?

    # To be safe, let's do from col 3 onwards if exists, else from USN col + 2 onwards
    startScoreCol = max(3, usnColIndex + 2)

    usnMap = {}
    for idx, row in data.iterrows():
        usn = row.iloc[usnColIndex]
        if not usn or not isinstance(usn, str):
            continue
        usn = usn.strip()
        if usn not in usnMap:
            usnMap[usn] = []
        usnMap[usn].append(row)

    resultRows = []
    for usn, rows in usnMap.items():
        maxScores = []
        # Collect max scores for all relevant columns
        for colIndex in range(startScoreCol, len(headers)):
            colScores = []
            for r in rows:
                val = r.iloc[colIndex]
                try:
                    score = float(val)
                    colScores.append(score)
                except (ValueError, TypeError):
                    pass
            maxScore = max(colScores) if colScores else 0
            maxScores.append(maxScore)
        # Build result row: USN + max scores
        resultRows.append([usn] + maxScores)

    # Build result dataframe headers: USN + relevant score columns headers
    resultHeaders = [headers[usnColIndex]] + headers[startScoreCol:]

    outputDf = pd.DataFrame(resultRows, columns=resultHeaders)

    st.success("✅ Max scores computed successfully!")

    # Download button
    originalName = uploadedFile.name
    if '.' in originalName:
        baseName = originalName.rsplit('.', 1)[0]
    else:
        baseName = originalName

    outputFileName = f"maxscores_{baseName}.xlsx"

    towrite = BytesIO()
    outputDf.to_excel(towrite, index=False)
    towrite.seek(0)

    st.download_button(
        label="📥 Download MaxScores Excel File",
        data=towrite,
        file_name=outputFileName,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
