import streamlit as st
import pandas as pd
import re
import io
import base64
import os

st.set_page_config(page_title="Max Scores Extractor", layout="centered")
st.title("Question-wise Max Scores Per USN")

uploadedFile = st.file_uploader("Upload Excel File (.xls or .xlsx)", type=["xls", "xlsx"])

if uploadedFile:
    try:
        # Read Excel file
        if uploadedFile.name.endswith(".xls"):
            import xlrd
            df = pd.read_excel(uploadedFile, engine='xlrd', header=None)
        else:
            df = pd.read_excel(uploadedFile, engine='openpyxl', header=None)

        # Auto-detect USN row
        usnPattern = re.compile(r'\b1[a-z]{2}\d{2}[a-z]{2,3}\d{3}\b', re.I)
        usnRowIdx = None
        for i, row in df.iterrows():
            if any(re.search(usnPattern, str(cell)) for cell in row):
                usnRowIdx = i
                break

        if usnRowIdx is None:
            st.error("USN row not found.")
        else:
            # Set header and extract data
            df.columns = df.iloc[usnRowIdx - 1]
            df = df.iloc[usnRowIdx:]
            df = df.reset_index(drop=True)

            st.markdown("### First 5 Rows of Input File")
            st.dataframe(df.head(5))

            # Compute max score for each USN
            result = []
            columns = df.columns.tolist()
            result.append(columns)

            for i in range(len(df)):
                row = df.iloc[i]
                rowDict = {}
                for col in columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        rowDict[col] = row[col]
                    else:
                        rowDict[col] = row[col]
                result.append(rowDict)

            output_df = pd.DataFrame(result[1:], columns=result[0])

            # Remove evaluator-related columns
            filtered_columns = [col for col in output_df.columns if not re.search(r"eval.*|evaluator", str(col), re.I)]
            output_df = output_df[filtered_columns]

            # Download link
            towrite = io.BytesIO()
            with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
                output_df.to_excel(writer, index=False, sheet_name='MaxScores')
                writer.save()
            towrite.seek(0)

            st.success("✅ Max scores computed successfully.")
            st.download_button(
                label="📥 Download MaxScores Excel File",
                data=towrite,
                file_name="maxscores_filename.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
