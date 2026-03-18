import re
import pandas as pd
import streamlit as st
import pdfplumber


def parse_paytm_pdf(file):

    # Extract all text from every page
    all_text = ""

    # Try opening without password first
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"

    except Exception as e:
        st.warning("🔒 This PDF appears to be password protected.")
        password = st.text_input(
            "Enter PDF password to continue:",
            type="password"
        )
        if not password:
            st.info(
                "Enter the password above or upload "
                "a non-password protected version."
            )
            return pd.DataFrame()

        try:
            with pdfplumber.open(file, password=password) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
        except:
            st.error("❌ Incorrect password. Please try again.")
            return pd.DataFrame()

    transactions = []

    # Split text into lines
    lines = all_text.split("\n")
    lines = [line.strip() for line in lines if line.strip()]

    # Date pattern
    date_pattern = re.compile(
        r'^(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        r'(?:\s+\d{4})?(?:\s+\d{1,2}:\d{2}(?:\s*[AP]M)?)?'
        r'|\d{1,2}/\d{1,2}/\d{2,4}(?:\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)?)',
        re.IGNORECASE
    )

    # Amount pattern
    amount_pattern = re.compile(
        r'([+-])\s*Rs\.[\d,]+(?:\.\d{1,2})?',
        re.IGNORECASE
    )

    # UPI ref pattern
    upi_pattern = re.compile(
        r'UPI\s+Ref\s+No[:\s]+(\d+)',
        re.IGNORECASE
    )

    # Tag pattern
    tag_pattern = re.compile(
        r'#\s*([A-Za-z\s]+)',
        re.IGNORECASE
    )

    i = 0
    while i < len(lines):
        line = lines[i]

        date_match = date_pattern.match(line)

        if date_match:
            # Skip summary lines
            if any(skip in line for skip in [
                "Payments made", "Payments received",
                "Total Money", "Paytm Statement",
                "FEB'", "MAR'", "JAN'", "APR'",
                "MAY'", "JUN'", "JUL'", "AUG'",
                "SEP'", "OCT'", "NOV'", "DEC'"
            ]):
                i += 1
                continue

        if date_match:
            transaction_lines = [line]
            j = i + 1

            while j < len(lines):
                next_line = lines[j]
                if date_pattern.match(next_line):
                    break
                if any(skip in next_line for skip in [
                    "Passbook Payments History",
                    "All payments done",
                    "Date &",
                    "Transaction Details",
                    "Notes & Tags",
                    "Your Account",
                    "Page ",
                    "For any queries",
                    "Contact Us",
                    "Powered by",
                    "Payments made",
                    "Payments received",
                    "Paytm Statement",
                    "Total Money"
                ]):
                    break
                transaction_lines.append(next_line)
                j += 1

            full_text = " ".join(transaction_lines)

            # Extract date and time
            date_time = date_match.group(0).strip()

            # Extract amount
            amount_match = amount_pattern.search(full_text)
            if not amount_match:
                i = j
                continue

            amount_str = amount_match.group(0).strip()
            sign = -1 if "-" in amount_str else 1
            amount_clean = re.sub(
                r'Rs\.', '', amount_str,
                flags=re.IGNORECASE
            )
            amount_clean = re.sub(r'[^\d.]', '', amount_clean)
            try:
                amount = sign * float(amount_clean)
            except:
                amount = 0

            # Extract tag
            tag_match = tag_pattern.search(full_text)
            tag = tag_match.group(1).strip() if tag_match else "Other"

            # Extract UPI ref
            upi_match = upi_pattern.search(full_text)
            upi_ref = upi_match.group(1) if upi_match else ""

            # Extract merchant name by elimination
            merchant_text = full_text
            merchant_text = re.sub(
                date_pattern, "", merchant_text
            )
            merchant_text = re.sub(
                r'UPI\s+ID:.*?(?=\s+UPI|\s+Tag|$)',
                "", merchant_text, flags=re.IGNORECASE
            )
            merchant_text = re.sub(
                r'UPI\s+Ref\s+No:.*?(?=\s+Tag|$)',
                "", merchant_text, flags=re.IGNORECASE
            )
            merchant_text = re.sub(
                r'Tag:.*$', "", merchant_text,
                flags=re.IGNORECASE
            )
            merchant_text = re.sub(
                r'Bank\s+Of.*$', "", merchant_text,
                flags=re.IGNORECASE
            )
            merchant_text = re.sub(
                amount_pattern, "", merchant_text
            )
            merchant_text = re.sub(
                r'Note:.*?(?=\s+Tag|$)', "",
                merchant_text, flags=re.IGNORECASE
            )
            merchant_text = re.sub(
                r'A/c\s+No:.*?(?=\s+UPI|$)', "",
                merchant_text, flags=re.IGNORECASE
            )
            merchant_name = " ".join(
                merchant_text.split()
            ).strip()

            transactions.append({
                "Date & Time": date_time,
                "Transaction Details": merchant_name,
                "Notes & Tags": tag,
                "Amount": amount,
                "UPI Ref": upi_ref
            })

            i = j
        else:
            i += 1

    if not transactions:
        st.warning(
            "Could not parse transactions from PDF. "
            "Try Excel format."
        )
        return pd.DataFrame()

    df = pd.DataFrame(transactions)
    st.success(
        f"Successfully parsed {len(df)} "
        f"transactions from PDF!"
    )
    return df