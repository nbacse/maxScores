import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Question-wise Max Scores Per USN")
st.write("Upload an Excel file to compute the question-wise maximum scores for each USN.")

uploadedFile = st.file_uploader("Choose an Excel file", type=["xlsx"])

# 🔍 Detect the row index where USNs start
def detect_usn_row_index(df):
    pattern = re.compile(r"1[A-Z]{2}\d{0,2}", re.IGNORECASE)
    for i, row in df.iterrows():
        if row.astype(str).apply(lambda x: bool(pattern.search(x))).any():
            return i
    return None

# 🔍 Find the column containing USNs
def find_usn_column(df):
    pattern = re.compile(r"1[A-Z]{2}\d{0,2}", re.IGNORECASE)
    for col in df.columns:
        if df[col].astype(str).apply(lambda x: bool(pattern.search(x))).any():
            return col
    return None

if uploadedFile:
    try:
        # Load raw data without headers
        dfRaw = pd.read_excel(uploadedFile, header=None)
        usnRowIndex = detect_usn_row_index(dfRaw)

        if usnRowIndex is None or usnRowIndex == 0:
            st.error("Unable to detect USN pattern or no header row above detected USNs.")
        else:
            headerRowIndex = usnRowIndex - 1
            df = pd.read_excel(uploadedFile, header=headerRowIndex)

            usnCol = find_usn_column(df)
            if usnCol is None:
                st.error("Could not identify the USN column.")
            else:
                scoreCols = df.columns[df.columns.get_loc(usnCol)+1:]
                resultRows = []

                for usn, group in df.groupby(usnCol):
                    row = {usnCol: usn}
                    for col in scoreCols:
                        row[col] = pd.to_numeric(group[col], errors='coerce').max()
                    resultRows.append(row)

                resultDf = pd.DataFrame(resultRows)

                # 🧹 Remove columns B and C if they exist
                if resultDf.shape[1] >= 3:
                    resultDf.drop(resultDf.columns[[1, 2]], axis=1, inplace=True)

                st.success("Max scores calculated successfully!")
                st.dataframe(resultDf)

                # 📤 Prepare Excel download
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    resultDf.to_excel(writer, index=False, sheet_name='Max Scores')
                output.seek(0)

                originalName = uploadedFile.name.rsplit(".", 1)[0]
                downloadFileName = f"maxscores_{originalName}.xlsx"

                st.download_button(
                    label="📥 Download Result Excel",
                    data=output,
                    file_name=downloadFileName,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"An error occurred: {e}")
