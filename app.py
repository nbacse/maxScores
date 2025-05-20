import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Max Scores Per USN")
st.write("Upload an Excel file to compute the maximum scores for each USN.")

uploadedFile = st.file_uploader("Choose an Excel file", type=["xlsx"])

def find_usn_column(df):
    for col in df.columns:
        if df[col].astype(str).str.contains(r"1BY21", case=False).any():
            return col
    return None

if uploadedFile:
    try:
        df = pd.read_excel(uploadedFile)

        usnCol = find_usn_column(df)
        if not usnCol:
            st.error("Could not find a USN column with pattern '1BY21'. Please check your file.")
        else:
            scoreCols = df.columns[df.columns.get_loc(usnCol)+1:]  # All columns after USN are assumed scores

            resultRows = []
            for usn, group in df.groupby(usnCol):
                row = {usnCol: usn}
                for col in scoreCols:
                    row[col] = pd.to_numeric(group[col], errors='coerce').max()
                resultRows.append(row)

            resultDf = pd.DataFrame(resultRows)

            # ✅ Drop columns B and C (second and third columns)
            if resultDf.shape[1] >= 3:
                resultDf.drop(resultDf.columns[[1, 2]], axis=1, inplace=True)

            st.success("Max scores calculated successfully!")
            st.dataframe(resultDf)

            # Generate downloadable Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                resultDf.to_excel(writer, index=False, sheet_name='Max Scores')

            output.seek(0)

            # ✅ Extract filename without extension
            originalName = uploadedFile.name.rsplit(".", 1)[0]
            downloadFileName = f"maxscores_{originalName}.xlsx"

            st.download_button(
                label="📥 Download MaxScores Excel File",
                data=output,
                file_name=downloadFileName,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")
