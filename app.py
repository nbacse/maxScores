import streamlit as st
import pandas as pd
import re
import base64
from io import BytesIO

st.set_page_config(page_title="Max Scores Per USN", layout="wide")
st.markdown("<h2 style='text-align: center;'>Question-wise Max Scores Per USN</h2>", unsafe_allow_html=True)

uploadedFile = st.file_uploader("Upload Excel File", type=["xlsx", "xls"], help="Limit: 200MB per file")

def detect_header_row(df):
    for idx, row in df.iterrows():
        row_str = row.astype(str).str.lower()
        if row_str.str.contains("usn").any() or row_str.str.contains(r"1[a-z]{2}\d{2}[a-z]{2}\d{3}", regex=True).any():
            return idx
    return None

if uploadedFile:
    try:
        dfList = pd.read_excel(uploadedFile, sheet_name=None, header=None)
        firstSheet = list(dfList.keys())[0]
        rawData = dfList[firstSheet]
        
        headerRow = detect_header_row(rawData)
        if headerRow is None:
            st.error("❌ Could not detect header row. Please check the uploaded file format.")
        else:
            data = pd.read_excel(uploadedFile, sheet_name=firstSheet, header=headerRow)
            st.success("✅ Max scores computed successfully!")

            # Show preview of input
            with st.expander("📄 Preview of Input File"):
                st.dataframe(data.head(5))

            # Detect USN column
            usnCol = next((col for col in data.columns if re.search(r'usn', str(col), re.I)), None)
            if not usnCol:
                st.error("❌ USN column not found.")
            else:
                # Clean USN values
                data[usnCol] = data[usnCol].astype(str).str.extract(r'(1[a-zA-Z]{2,4}\d{2}[a-zA-Z]{2,3}\d{3})', expand=False)
                data = data.dropna(subset=[usnCol])

                # Drop evaluator-related columns ONLY
                dropCols = [col for col in data.columns if re.search(r'(evaluator|eval[_ ]?version)', str(col), re.I)]
                cleanedData = data.drop(columns=dropCols, errors='ignore')

                # Group and compute max
                maxScores = cleanedData.groupby(usnCol, as_index=False).max(numeric_only=True)

                st.subheader("📊 Max Scores Per USN")
                st.dataframe(maxScores)

                # Prepare downloadable Excel
                def to_excel_download(df):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    return output.getvalue()

                excelBytes = to_excel_download(maxScores)
                b64 = base64.b64encode(excelBytes).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="MaxScoresPerUSN.xlsx">📥 Download Max Scores Excel File</a>'
                st.markdown(href, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Failed to process the file. Error: {e}")
