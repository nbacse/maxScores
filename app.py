import streamlit as st
import pandas as pd
import re
import base64
from io import BytesIO

st.set_page_config(page_title="Max Scores Per USN", layout="wide")
st.markdown("<h2 style='text-align: center;'>Question-wise Max Scores Per USN</h2>", unsafe_allow_html=True)

uploadedFile = st.file_uploader("Upload Excel File", type=["xlsx", "xls"], help="Limit: 200MB per file - XLSX, XLS")

if uploadedFile is not None:
    try:
        # Read sheet with no headers to detect them manually
        dfList = pd.read_excel(uploadedFile, sheet_name=None, header=None)
        firstSheet = list(dfList.keys())[0]
        rawData = dfList[firstSheet]

        # Identify header row as the row ABOVE the first USN match
        headerRow = None
        usnPattern = re.compile(r'1[A-Z]{2,4}\d{2}[A-Z]{2,3}\d{3}', re.I)
        for idx in range(1, len(rawData)):
            row = rawData.iloc[idx]
            if row.astype(str).apply(lambda x: bool(usnPattern.search(str(x)))).any():
                headerRow = idx - 1  # row above is the header
                break

        if headerRow is not None:
            data = pd.read_excel(uploadedFile, sheet_name=firstSheet, header=headerRow)
        else:
            st.error("❌ Could not detect header row. Please check the uploaded file format.")
            st.stop()

        st.success("✅ Max scores computed successfully!")

        # Show preview
        with st.expander("📄 Preview of Input File"):
            st.dataframe(data.head(10))

        # Identify USN column
        usnCol = next((col for col in data.columns if re.search(r'usn', str(col), re.I) or
                       data[col].astype(str).apply(lambda x: bool(usnPattern.fullmatch(str(x)))).sum() > 0), None)

        if not usnCol:
            st.error("❌ USN column not found.")
            st.stop()

        # Clean and normalize USN values
        data[usnCol] = data[usnCol].astype(str).str.extract(usnPattern, expand=False)
        data = data.dropna(subset=[usnCol])

        # Drop evaluator and version columns (if any)
        colsToDrop = [col for col in data.columns if re.search(r'(evaluator|eval[_ ]?version)', str(col), re.I)]
        cleanedData = data.drop(columns=colsToDrop, errors='ignore')

        # Compute max scores
        maxScores = cleanedData.groupby(usnCol, as_index=False).max(numeric_only=True)

        st.subheader("📊 Max Scores Per USN")
        st.dataframe(maxScores)

        # Download button
        def to_excel(df):
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            return output.getvalue()

        excelData = to_excel(maxScores)
        b64 = base64.b64encode(excelData).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="MaxScoresPerUSN.xlsx">📥 Download Max Scores Excel File</a>'
        st.markdown(href, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Failed to process the file. Error: {e}")
