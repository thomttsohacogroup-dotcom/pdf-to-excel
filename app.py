import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Drug Excel Mapper", layout="centered")

st.title("💊 Drug Data Mapper")
st.write("Upload Excel → Clean → Auto Map → Export")

# ===== TARGET SCHEMA (DƯỢC) =====
TARGET_COLUMNS = [
    "STT",
    "Tên thuốc",
    "Hoạt chất",
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
        st.error(f"Lỗi đọc file: {e}")
        return None


def clean_data(df):
    # Xoá ô rỗng giả
    df = df.replace(r'^\s*$', None, regex=True)

    # Xoá dòng trống
    df = df.dropna(how="all")

    # Xoá cột trống
    df = df.dropna(axis=1, how="all")

    # Fix merged cell
    df = df.ffill()

    # Trim text
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()

    return df


def auto_map_columns(input_columns):
    mapping = {}

    column_alias = {
        "STT": ["stt", "số thứ tự"],
        "Tên thuốc": ["tên thuốc", "drug name", "product name"],
        "Hoạt chất": ["hoạt chất", "thành phần", "active ingredient"],
        "Dạng bào chế": ["dạng bào chế", "dosage form"],
        "Quy cách đóng gói": ["quy cách", "đóng gói", "packaging"],
        "Tiêu chuẩn": ["tiêu chuẩn", "standard"],
        "Tuổi thọ (tháng)": ["tuổi thọ", "hạn dùng", "shelf life"],
        "Số đăng ký": ["số đăng ký", "registration number", "sdk"],
        "Cơ sở đăng ký": ["cơ sở đăng ký", "marketing authorization holder"],
        "Cơ sở sản xuất": ["cơ sở sản xuất", "manufacturer"]
    }

    for target, aliases in column_alias.items():
        for col in input_columns:
            col_lower = str(col).lower()
            if any(alias in col_lower for alias in aliases):
                mapping[target] = col
                break

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


def split_active_ingredient(df):
    # Tách "Hoạt chất - Hàm lượng"
    if "Hoạt chất" in df.columns:
        try:
            split_df = df["Hoạt chất"].str.split("-", n=1, expand=True)
            if split_df.shape[1] == 2:
                df["Hoạt chất"] = split_df[0].str.strip()
                df["Hàm lượng"] = split_df[1].str.strip()
        except:
            pass
    return df


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
        st.subheader("🔍 Preview dữ liệu gốc")
        st.dataframe(df.head(10))

        df_clean = clean_data(df)

        st.subheader("🧹 Sau khi làm sạch")
        st.dataframe(df_clean.head(10))

        mapping = auto_map_columns(df_clean.columns)

        st.subheader("🔗 Auto Mapping")
        st.write(mapping)

        if st.button("🚀 Xử lý dữ liệu"):
            with st.spinner("Đang xử lý..."):
                try:
                    df_mapped = map_columns(df_clean, mapping)

                    # Optional: tách hoạt chất
                    df_mapped = split_active_ingredient(df_mapped)

                    st.subheader("✅ Kết quả")
                    st.dataframe(df_mapped.head(10))

                    output = export_excel(df_mapped)

                    st.success("Xử lý thành công!")

                    st.download_button(
                        label="📥 Tải file Excel",
                        data=output,
                        file_name="drug_result.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                except Exception as e:
                    st.error(f"Lỗi xử lý: {e}")

else:
    st.info("👉 Vui lòng upload file Excel để bắt đầu")