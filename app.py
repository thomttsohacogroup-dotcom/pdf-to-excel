import streamlit as st
import pandas as pd
import pdfplumber
import io

st.set_page_config(page_title="PDF to Excel", layout="centered")

st.title("📄 PDF to Excel Converter")
st.write("Upload file PDF có bảng → xuất ra Excel")

# Upload file
uploaded_file = st.file_uploader("Chọn file PDF", type="pdf")

# Mapping cột (bạn có thể chỉnh lại nếu cần)
COLUMN_MAPPING = {
    'STT': 'No.',
    'Họ và Tên': 'Full Name'
}

def extract_tables_from_pdf(file):
    all_tables = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 1:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    all_tables.append(df)

    return all_tables

def process_tables(tables):
    if not tables:
        return None

    combined_df = pd.concat(tables, ignore_index=True)
    combined_df = combined_df.rename(columns=COLUMN_MAPPING)

    return combined_df

if uploaded_file is not None:
    st.success("✅ Upload thành công!")

    if st.button("🚀 Xử lý PDF"):
        with st.spinner("Đang xử lý..."):
            tables = extract_tables_from_pdf(uploaded_file)
            df = process_tables(tables)

            if df is not None:
                st.subheader("📊 Kết quả:")
                st.dataframe(df)

                # Xuất Excel
                output = io.BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)

                st.download_button(
                    label="📥 Tải file Excel",
                    data=output,
                    file_name="result.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("❌ Không tìm thấy bảng trong PDF")