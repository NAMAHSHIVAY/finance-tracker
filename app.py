import streamlit as st
from parsers.excel_parser import parse_excel
from parsers.pdf_paytm import parse_paytm_pdf
from processors.cleaner import clean_excel_data
from processors.categoriser import add_categories
from analysis.charts import show_analysis

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────

st.set_page_config(
    page_title="Finance Tracker — Nitin Builds",
    page_icon="💰",
    layout="wide"
)

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────

st.title("💰 Personal Finance Tracker")
st.subheader(
    "Upload your bank statement — "
    "know exactly where your money goes."
)
st.markdown("---")

# ─────────────────────────────────────────
# FILE UPLOADER
# ─────────────────────────────────────────

uploaded_file = st.file_uploader(
    "Upload your bank statement (PDF or Excel)",
    type=["pdf", "xlsx", "xls"]
)

st.caption(
    "✅ Supported: Paytm PDF, All bank Excel files | "
    "🔜 Coming soon: PhonePe, GPay PDFs"
)

if uploaded_file is None:
    st.info("👆 Upload your bank statement above to get started.")
    st.stop()

# ─────────────────────────────────────────
# FILE DETECTION AND PARSING
# ─────────────────────────────────────────

file_name = uploaded_file.name

if file_name.endswith(".pdf"):
    df = parse_paytm_pdf(uploaded_file)

elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
    df = parse_excel(uploaded_file)
    df = clean_excel_data(df)
    st.success(f"Successfully parsed {len(df)} transactions!")

else:
    st.error(
        "Unsupported file format. "
        "Please upload a PDF or Excel file."
    )
    st.stop()

if df.empty:
    st.stop()

# ─────────────────────────────────────────
# CATEGORISE
# ─────────────────────────────────────────

df = add_categories(df)

# ─────────────────────────────────────────
# RAW DATA
# ─────────────────────────────────────────

with st.expander("📋 View Raw Transaction Data"):
    st.dataframe(df)

# ─────────────────────────────────────────
# ANALYSIS
# ─────────────────────────────────────────

show_analysis(df)