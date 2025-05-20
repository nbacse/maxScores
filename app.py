import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Max Scores", layout="centered")
st.title("Question-wise Max Scores Per USN")

uploadedFile = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if uploadedFile:
    # Detect file extension
    fileExtension = uploadedFile.name.split(".")[-1].lower()

    # Read Excel based on extension
    if fileExtension == "xls":
        df = pd.read_excel(uploadedFile, engine="xlrd")
    else:
        df = pd.read_excel(uploadedFile, engine="openpyxl")

    # Show top 5 rows of uploaded file
    st.subheader("Preview of Uploaded File:")
    st.dataframe(df.head())

    # Find the header row and USN column
    usnRegex = re.compile(r"1[a-zA-Z]{2}\d{2}", re.IGNORECASE)
    headerRow = None
    usnColIndex = None

    for i, row in df.iterrows():
        for j, cell in enumerate(row):
            if isinstance(cell, str) and usnRegex.search(cell):
                headerRow = i - 1
                usnColIndex = j
                break
        if headerRow is not None:
            break

    if headerRow is not None:
        df.columns = df.iloc[headerRow]
        df = df.iloc[headerRow + 1:]
        df = df.reset_index(drop=True)
        df = df.dropna(subset=[df.columns[usnColIndex]])

        usnColName = df.columns[usnColIndex]
        allHeaders = df.columns.tolist()

        grouped = df.groupby(usnColName)
        output = pd.DataFrame(columns=allHeaders)

        for usn, group in grouped:
            rowDict = {usnColName: usn}
            for col in allHeaders:
                if col == usnColName:
                    continue
                try:
                    numericValues = pd.to_numeric(group[col], errors='coerce')
                    maxVal = numericValues.max()
                    if pd.notna(maxVal):
                        rowDict[col] = maxVal
                    else:
                        rowDict[col] = ""
                except:
                    rowDict[col] = ""
            output = pd.concat([output, pd.DataFrame([rowDict])], ignore_index=True)

        # Write to Excel
        outputFile = BytesIO()
        originalName = uploadedFile.name.rsplit(".", 1)[0]
        fileName = f"maxscores_{originalName}.xlsx"

        with pd.ExcelWriter(outputFile, engine="openpyxl") as writer:
            output.to_excel(writer, index=False)

        # ✅ Success message
        st.success("✅ Max scores computed successfully!")

        st.download_button(
            label="📥 Download MaxScores Excel File",
            data=outputFile.getvalue(),
            file_name=fileName,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("❌ Could not detect USN column (e.g., 1BY21, 1TD, 1TE, etc.). Please check your file.")
