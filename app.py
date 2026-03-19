import streamlit as st
import io
import pdfplumber
from parsers.excel_parser import parse_excel
from parsers.pdf_paytm import parse_paytm_pdf
from parsers.pdf_gpay import parse_gpay_pdf
from parsers.pdf_phonepe import parse_phonepe_pdf
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
    "✅ Supported: Paytm PDF, GPay PDF, PhonePe PDF, "
    "All bank Excel files"
)

st.caption(
    "🔒 Privacy: Your data is processed in memory only. "
    "Nothing is stored or saved anywhere."
)

# ─────────────────────────────────────────
# BUDGET INPUT
# ─────────────────────────────────────────

st.markdown("### 💰 Monthly Budget (Optional)")
col_sal1, col_sal2 = st.columns([2, 1])

with col_sal1:
    budget = st.number_input(
        "Set your monthly spending budget (optional)",
        min_value=0,
        value=0,
        step=1000,
        help="Set how much you plan to spend this month. "
             "We will show how much you have used."
    )

with col_sal2:
    budget_label = st.empty()
    if budget > 0:
        budget_label.success(f"✅ Budget set: ₹{budget:,.0f}/month")

st.markdown("---")

if uploaded_file is None:
    st.info("👆 Upload your bank statement above to get started.")
    st.stop()

# ─────────────────────────────────────────
# FILE DETECTION AND PARSING
# ─────────────────────────────────────────

file_name = uploaded_file.name

if file_name.endswith(".pdf"):
    try:
        # Read file bytes once
        file_bytes = uploaded_file.read()

        # Detect PDF type by filename first then content
        pdf_type = "unknown"
        file_name_lower = file_name.lower()

        if "gpay" in file_name_lower or "google" in file_name_lower:
            pdf_type = "gpay"
        elif "paytm" in file_name_lower:
            pdf_type = "paytm"
        elif "phonepe" in file_name_lower or "phone_pe" in file_name_lower:
            pdf_type = "phonepe"
        else:
            # Fall back to content detection
            try:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    first_page = pdf.pages[0].extract_text()
                    if first_page:
                        first_page_lower = first_page.lower()
                        if "google" in first_page_lower:
                            pdf_type = "gpay"
                        elif "paytm" in first_page_lower:
                            pdf_type = "paytm"
                        elif "phonepe" in first_page_lower:
                            pdf_type = "phonepe"
            except:
                pass

        # Parse using correct parser
        if pdf_type == "gpay":
            df = parse_gpay_pdf(io.BytesIO(file_bytes))
        elif pdf_type == "paytm":
            df = parse_paytm_pdf(io.BytesIO(file_bytes))
        elif pdf_type == "phonepe":
            df = parse_phonepe_pdf(io.BytesIO(file_bytes))
        else:
            st.warning(
                "⚠️ Could not detect PDF type automatically. "
                "Trying Paytm format..."
            )
            df = parse_paytm_pdf(io.BytesIO(file_bytes))

    except Exception as e:
        st.error(
            "❌ Could not parse this PDF. "
            "Please make sure it is a supported statement. "
            "For other banks please upload Excel format."
        )
        st.stop()

elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
    try:
        df = parse_excel(uploaded_file)
        df = clean_excel_data(df)
        st.success(f"Successfully parsed {len(df)} transactions!")
    except Exception as e:
        st.error(
            "❌ Could not parse this PDF. "
            "Please make sure it is a supported statement. "
            "For other banks please upload Excel format."
        )
        st.stop()

else:
    st.error(
        "❌ Unsupported file format. "
        "Please upload a PDF or Excel file."
    )
    st.stop()

if df.empty:
    st.warning(
        "⚠️ No transactions found in this file. "
        "Please check if you uploaded the correct statement."
    )
    st.stop()

if "Amount" not in df.columns:
    st.warning(
        "⚠️ Could not detect Amount column. "
        "Please DM us on Instagram @nitinbuilds.official "
        "with your bank name and we will add support within 48 hours."
    )
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

show_analysis(df, budget)