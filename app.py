import streamlit as st
import pandas as pd
import re
import tempfile
import os

st.set_page_config(page_title="Max Scores", layout="wide")
st.title("Question-wise Max Scores Per USN")

uploadedFile = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
if uploadedFile is not None:
    try:
        # Use temporary file to handle .xls as well
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xls") as tmp:
            tmp.write(uploadedFile.read())
            tmpPath = tmp.name

        # Read all sheets
        excelFile = pd.ExcelFile(tmpPath, engine="xlrd" if uploadedFile.name.endswith(".xls") else None)
        sheet = excelFile.parse(excelFile.sheet_names[0], header=None)

        # Detect USN row
        usnRowIndex = None
        for i in range(min(20, len(sheet))):
            if sheet.iloc[i].astype(str).str.contains(r"\b1[a-zA-Z]{2}\d{2}", regex=True).any():
                usnRowIndex = i
                break

        if usnRowIndex is None:
            st.error("❌ Could not detect USN row.")
        else:
            # Set headers
            sheet.columns = sheet.iloc[usnRowIndex - 1]
            data = sheet.iloc[usnRowIndex:]

            st.info("✅ Max scores computed successfully!")
            st.subheader("📄 Preview of Input File")
            st.dataframe(data.head(5))

            usnCol = next((col for col in data.columns if str(col).lower().startswith("usn")), None)
            if not usnCol:
                st.error("❌ USN column not found.")
            else:
                usns = data[usnCol].astype(str).str.extract(r'(1[a-zA-Z]{2,4}\d{2}\w{2,3}\d{3})', expand=False)
                data[usnCol] = usns
                data = data.dropna(subset=[usnCol])

                # Numeric columns
                numericCols = data.select_dtypes(include='number').columns

                output = pd.DataFrame()
                for _, row in data.iterrows():
                    maxScores = row[numericCols]
                    maxDict = maxScores.to_dict()
                    rowDict = {usnCol: row[usnCol], **maxDict}
                    output = pd.concat([output, pd.DataFrame([rowDict])], ignore_index=True)

                # Insert all columns from original sheet in the same order
                allCols = data.columns
                nonEvalCols = [col for col in allCols if not re.search(r"eval.*|evaluator", str(col), re.I)]

                # Reorder final output to match input columns (excluding evaluator-related)
                output = output[[col for col in nonEvalCols if col in output.columns]]

                # File name
                originalName = uploadedFile.name.rsplit(".", 1)[0]
                downloadName = f"maxscores_{originalName}.xlsx"

                # Save and offer download
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmpOut:
                    output.to_excel(tmpOut.name, index=False)
                    st.download_button(
                        label="📥 Download MaxScores Excel File",
                        data=open(tmpOut.name, "rb").read(),
                        file_name=downloadName,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        if os.path.exists(tmpPath):
            os.remove(tmpPath)
