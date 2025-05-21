import streamlit as st
import pandas as pd
import re
import base64

st.set_page_config(page_title="Max Scores Per USN", layout="wide")
st.markdown("""
    <h2 style='text-align: center;'>Question-wise Max Scores Per USN</h2>
""", unsafe_allow_html=True)

uploadedFile = st.file_uploader("Upload Excel File", type=["xlsx", "xls"], help="Limit: 200MB per file - XLSX, XLS")
data = None

if uploadedFile is not None:
    try:
        # Try reading the Excel file without assuming header
        dfList = pd.read_excel(uploadedFile, sheet_name=None, header=None)
        firstSheet = list(dfList.keys())[0]
        rawData = dfList[firstSheet]

        # Identify the header row by looking for 'USN' or USN-like pattern
        headerRow = None
        for idx, row in rawData.iterrows():
            if row.astype(str).str.contains(r'\busn\b', case=False, na=False).any():
                headerRow = idx
                break

        if headerRow is not None:
            data = pd.read_excel(uploadedFile, sheet_name=firstSheet, header=headerRow)
        else:
            st.error("Could not detect header row. Please check the uploaded file format.")
            st.stop()

        if data is not None:
            st.success("✅ Max scores computed successfully!")

            # Display preview
            with st.expander("📄 Preview of Input File"):
                st.dataframe(data.head(10))

            # Prepare regex pattern
            usnPatternStr = r'(1[A-Z]{2,4}\d{2}[A-Z]{2,3}\d{3})'
            usnPattern = re.compile(usnPatternStr, re.I)

            # Detect USN column by name or content
            usnCol = next((col for col in data.columns if re.search(r'usn', str(col), re.I) or
                           data[col].astype(str).apply(lambda x: bool(usnPattern.fullmatch(str(x)))).sum() > 0), None)

            if not usnCol:
                st.error("❌ USN column not found.")
                st.stop()

            # Clean USN values
            data[usnCol] = data[usnCol].astype(str).str.extract(usnPatternStr, expand=False)
            data = data.dropna(subset=[usnCol])

            # Remove unwanted columns with names like evaluator, eval_version, etc.
            removeCols = [col for col in data.columns if re.search(r'(evaluator|eval[_ ]?version)', str(col), re.I)]
            cleanedData = data.drop(columns=removeCols)

            # Group by USN and get max of each column
            maxScores = cleanedData.groupby(usnCol, as_index=False).max(numeric_only=True)

            st.subheader("📊 Max Scores Per USN")
            st.dataframe(maxScores)

            # Download button
            def convert_df(df):
                return df.to_excel(index=False, engine='openpyxl')

            excelBytes = convert_df(maxScores)
            b64 = base64.b64encode(excelBytes).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="MaxScoresPerUSN.xlsx">📥 Download Max Scores Excel File</a>'
            st.markdown(href, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Failed to process the file. Error: {e}")