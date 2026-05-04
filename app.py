import streamlit as st
import pandas as pd
import io

# Optional fuzzy matching
try:
    from rapidfuzz import process, fuzz
    FUZZY_AVAILABLE = True
except:
    FUZZY_AVAILABLE = False

st.set_page_config(page_title="Excel Mapper", layout="centered")

st.title("📊 Excel Data Mapper")
st.write("Upload Excel → Clean → Map → Export")

# ===== TARGET SCHEMA =====
TARGET_COLUMNS = [
    "STT",
    "Tên thuốc",
    "Hoạt chất chính - Hàm lượng",
    "Dạng bào chế",
    "Quy cách đóng gói",
    "Tiêu chuẩn",
    "Tuổi thọ (tháng)",
    "Số đăng ký",
    "Cơ sở đăng ký",
    "Cơ sở sản xuất"
]

# ===== FUNCTIONS =====

def load_excel(file):
    try:
        df = pd.read_excel(file)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


def clean_data(df):
    # Remove empty-like strings first
    df = df.replace(r'^\s*$', None, regex=True)

    # Remove empty rows
    df = df.dropna(how="all")

    # Remove empty columns
    df = df.dropna(axis=1, how="all")

    # Forward fill (fix merged cells - pandas 2.x safe)
    df = df.ffill()

    # Trim whitespace safely
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()

    return df


def auto_map_columns(input_columns):
    mapping = {}

    for target in TARGET_COLUMNS:
        # Exact match first
        for col in input_columns:
            if col and col.lower() == target.lower():
                mapping[target] = col

        # Fuzzy match
        if target not in mapping and FUZZY_AVAILABLE:
            match = process.extractOne(target, input_columns, scorer=fuzz.ratio)
            if match and match[1] > 70:
                mapping[target] = match[0]

    return mapping


def map_columns(df, mapping):
    new_df = pd.DataFrame()

    for target_col in TARGET_COLUMNS:
        source_col = mapping.get(target_col)

        if source_col and source_col in df.columns:
            new_df[target_col] = df[source_col]
        else:
            new_df[target_col] = None

    return new_df


def export_excel(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return output


# ===== UI =====

uploaded_file = st.file_uploader("📤 Upload Excel file", type=["xlsx"])

if uploaded_file:
    df = load_excel(uploaded_file)

    if df is not None:
        st.subheader("🔍 Preview (first 10 rows)")
        st.dataframe(df.head(10))

        df_clean = clean_data(df)

        st.subheader("🧹 Cleaned Data Preview")
        st.dataframe(df_clean.head(10))

        st.subheader("🔗 Column Mapping")

        auto_mapping = auto_map_columns(df_clean.columns)

        mapping = {}

        for target in TARGET_COLUMNS:
            default_value = auto_mapping.get(target, None)

            options = [None] + list(df_clean.columns)

            if default_value in df_clean.columns:
                default_index = options.index(default_value)
            else:
                default_index = 0

            mapping[target] = st.selectbox(
                f"Map '{target}'",
                options=options,
                index=default_index
            )

        if st.button("🚀 Process Data"):
            with st.spinner("Processing..."):
                try:
                    df_mapped = map_columns(df_clean, mapping)

                    st.subheader("✅ Result Preview")
                    st.dataframe(df_mapped.head(10))

                    output = export_excel(df_mapped)

                    st.success("Processing completed!")

                    st.download_button(
                        label="📥 Download Excel",
                        data=output,
                        file_name="result.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                except Exception as e:
                    st.error(f"Error during processing: {e}")

else:
    st.info("Please upload an Excel file to begin.")