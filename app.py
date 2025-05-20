import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Max Scores Per USN", layout="centered")
st.title("📊 Question-wise Max Scores Per USN")

uploadedFile = st.file_uploader("Upload Excel File (.xls or .xlsx)", type=["xls", "xlsx"])

if uploadedFile:
    try:
        if uploadedFile.name.endswith(".xls"):
            df = pd.read_excel(uploadedFile, engine="xlrd")
        else:
            df = pd.read_excel(uploadedFile)
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

    # Detect row where USNs start
    usnRowIndex = None
    usnColIndex = None
    usnPattern = re.compile(r"1[A-Z]{2}\d{0,2}", re.IGNORECASE)

    for i, row in df.iterrows():
        for j, cell in enumerate(row):
            if isinstance(cell, str) and usnPattern.match(cell.strip()):
                usnRowIndex = i
                usnColIndex = j
                break
        if usnRowIndex is not None:
            break

    if usnRowIndex is None:
        st.error("❌ Could not find USN pattern like '1BY22', '1TD', etc.")
        st.stop()

    # Assign headers from row above the USN row
    headers = df.iloc[usnRowIndex - 1].astype(str).tolist()
    
    # Handle duplicate column names
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

    headers = make_unique(headers)
    
    data = df.iloc[usnRowIndex:].copy()
    data.columns = headers
    data.reset_index(drop=True, inplace=True)

    st.subheader("📄 Preview of Uploaded Data")
    st.dataframe(data.head(5))

    usnColName = headers[usnColIndex]
    usnGroups = data.groupby(usnColName)

    outputRows = []

    for usn, group in usnGroups:
        scoresOnly = group.iloc[:, usnColIndex + 3:]
        maxScores = scoresOnly.max(numeric_only=True)
        rowDict = {usnColName: usn}
        rowDict.update(maxScores.to_dict())
        outputRows.append(rowDict)

    output = pd.DataFrame(outputRows)
    output = output[[usnColName] + [col for col in output.columns if col != usnColName]]

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        output.to_excel(writer, index=False, sheet_name="Max Scores")

    buffer.seek(0)
    originalName = uploadedFile.name.rsplit(".", 1)[0]
    downloadFileName = f"maxscores_{originalName}.xlsx"

    st.success("✅ Max scores computed successfully!")

    st.download_button(
        label="📥 Download MaxScores Excel File",
        data=buffer,
        file_name=downloadFileName,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
