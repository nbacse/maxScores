import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Max Scores Per USN", layout="centered")
st.title("📊 Question-wise Max Scores Per USN")

uploadedFile = st.file_uploader("Upload Excel File (.xls or .xlsx)", type=["xls", "xlsx"])

if uploadedFile:
    # Detect file type and read accordingly
    try:
        if uploadedFile.name.endswith(".xls"):
            df = pd.read_excel(uploadedFile, engine="xlrd")
        else:
            df = pd.read_excel(uploadedFile)
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

    # Find the row where USN starts (based on pattern)
    usnRowIndex = None
    usnColIndex = None
    usnPattern = re.compile(r"1[A-Z]{2}\d{2}", re.IGNORECASE)

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

    # Extract headers and data from the detected row
    headers = df.iloc[usnRowIndex - 1].tolist()
    data = df.iloc[usnRowIndex:].copy()
    data.columns = headers
    data.reset_index(drop=True, inplace=True)

    # Show top 5 rows of input data
    st.subheader("📄 Preview of Uploaded Data")
    st.dataframe(data.head(5))

    # Group by USN column
    usnGroups = data.groupby(data.columns[usnColIndex])
    outputRows = []

    for usn, group in usnGroups:
        scoresOnly = group.iloc[:, usnColIndex + 3:]  # Assuming scores start after column C
        maxScores = scoresOnly.max(numeric_only=True)
        rowDict = {data.columns[usnColIndex]: usn}
        rowDict.update(maxScores.to_dict())
        outputRows.append(rowDict)

    output = pd.DataFrame(outputRows)

    # Set column order: USN first, then scores
    output = output[[data.columns[usnColIndex]] + [col for col in output.columns if col != data.columns[usnColIndex]]]

    # Save to Excel
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
