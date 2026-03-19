import re
import pandas as pd
import streamlit as st
import pdfplumber

def parse_gpay_pdf(file):

    all_lines = []

    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                words = page.extract_words(
                    x_tolerance=3,
                    y_tolerance=3,
                    keep_blank_chars=False
                )
                if not words:
                    continue

                lines = {}
                for word in words:
                    y_key = round(word['top'] / 5) * 5
                    if y_key not in lines:
                        lines[y_key] = []
                    lines[y_key].append(word['text'])

                for y_key in sorted(lines.keys()):
                    line_text = " ".join(lines[y_key])
                    if line_text.strip():
                        all_lines.append(line_text.strip())

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
                    words = page.extract_words(
                        x_tolerance=3,
                        y_tolerance=3
                    )
                    if not words:
                        continue
                    lines = {}
                    for word in words:
                        y_key = round(word['top'] / 5) * 5
                        if y_key not in lines:
                            lines[y_key] = []
                        lines[y_key].append(word['text'])
                    for y_key in sorted(lines.keys()):
                        line_text = " ".join(lines[y_key])
                        if line_text.strip():
                            all_lines.append(line_text.strip())
        except:
            st.error("❌ Incorrect password. Please try again.")
            return pd.DataFrame()

    transactions = []

    # GPay puts date + merchant + amount on same line
    # Pattern: "13Nov,2025 PaidtoPURVAVIJAYBORA ₹150"
    # We look for lines containing ₹ symbol
    amount_pattern = re.compile(r'₹([\d,]+(?:\.\d{1,2})?)')
    upi_pattern = re.compile(r'UPITransactionID:(\d+)', re.IGNORECASE)
    
    # Date pattern — "13Nov,2025" no spaces
    date_pattern = re.compile(
        r'(\d{1,2}(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec),?\s*\d{4})',
        re.IGNORECASE
    )

    # Time pattern — "11:14AM"
    time_pattern = re.compile(
        r'(\d{1,2}:\d{2}\s*(?:AM|PM))',
        re.IGNORECASE
    )

    skip_lines = [
        "Transaction statement",
        "Transactionstatementperiod",
        "Date&time",
        "Page1of",
        "Note:This",
        "received.Any",
        "September2025",
        "February2026",
        "January", "March", "April",
        "October", "November", "December"
    ]

    i = 0
    while i < len(all_lines):
        line = all_lines[i]

        # Skip header and footer lines
        if any(skip in line for skip in skip_lines):
            i += 1
            continue

        # Check if line has ₹ — transaction line
        amount_match = amount_pattern.search(line)

        if amount_match:
            # Extract amount
            amount_str = amount_match.group(1).replace(",", "")
            try:
                amount = -float(amount_str)
            except:
                amount = 0

            # Extract date
            date_match = date_pattern.search(line)
            date_str = date_match.group(1) if date_match else ""

            # Extract merchant — text between date and amount
            merchant = line
            if date_str:
                merchant = merchant.replace(date_str, "")
            merchant = amount_pattern.sub("", merchant)
            merchant = re.sub(
                r'^(Paidto|Receivedfrom)\s*', "", merchant,
                flags=re.IGNORECASE
            )
            # Add spaces before capital letters for merged words
            merchant = re.sub(r'([a-z])([A-Z])', r'\1 \2', merchant)
            merchant = merchant.strip()

            # Check if received
            if "Receivedfrom" in line or "received from" in line.lower():
                amount = abs(amount)

            # Look at next line for time and UPI ref
            time_str = ""
            upi_ref = ""
            if i + 1 < len(all_lines):
                next_line = all_lines[i + 1]
                time_match = time_pattern.search(next_line)
                if time_match:
                    time_str = time_match.group(1)
                upi_match = upi_pattern.search(next_line)
                if upi_match:
                    upi_ref = upi_match.group(1)

            transactions.append({
                "Date & Time": f"{date_str} {time_str}".strip(),
                "Transaction Details": merchant,
                "Notes & Tags": "",
                "Amount": amount,
                "UPI Ref": upi_ref
            })

        i += 1

    if not transactions:
        st.warning(
            "Could not parse transactions from GPay PDF. "
            "Try Excel format if available."
        )
        return pd.DataFrame()

    df = pd.DataFrame(transactions)
    st.success(
        f"Successfully parsed {len(df)} "
        f"transactions from GPay PDF!"
    )
    return df