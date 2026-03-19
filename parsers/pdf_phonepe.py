import re
import pandas as pd
import streamlit as st
import pdfplumber


def parse_phonepe_pdf(file):

    all_text = ""

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
    
    lines = all_text.split("\n")
    lines = [line.strip() for line in lines if line.strip()]

    transactions = []

    # PhonePe puts date + merchant + type + amount on ONE line
    # Pattern: "Mar 18, 2026 Paid to NEERA DEVI DEBIT ₹27"
    
    # Main transaction line pattern
    txn_line_pattern = re.compile(
        r'^((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        r'\s+\d{1,2},\s+\d{4})\s+'
        r'(Paid to|Received from)\s+'
        r'(.+?)\s+'
        r'(DEBIT|CREDIT)\s+'
        r'₹([\d,]+(?:\.\d{1,2})?)$',
        re.IGNORECASE
    )

    # Time + Transaction ID line pattern
    time_txn_pattern = re.compile(
        r'^(\d{1,2}:\d{2}\s+(?:AM|PM))\s+Transaction\s+ID\s+(T\d+)$',
        re.IGNORECASE
    )

    # UTR pattern
    utr_pattern = re.compile(
        r'UTR\s+No\.\s+(\d+)',
        re.IGNORECASE
    )

    skip_lines = [
        "Transaction Statement",
        "Date Transaction Details",
        "Page ",
        "This is a system",
        "support.phonepe.com",
        "19 Mar, 2025",
        "19 Mar, 2026"
    ]

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip headers and footers
        if any(skip in line for skip in skip_lines):
            i += 1
            continue

        # Try to match main transaction line
        txn_match = txn_line_pattern.match(line)

        if txn_match:
            date_str = txn_match.group(1).strip()
            direction = txn_match.group(2).strip()
            merchant = txn_match.group(3).strip()
            txn_type = txn_match.group(4).strip()
            amount_str = txn_match.group(5).replace(",", "")

            try:
                amount = float(amount_str)
            except:
                amount = 0

            # Make negative for debit positive for credit
            if txn_type.upper() == "DEBIT":
                amount = -abs(amount)
            else:
                amount = abs(amount)

            # Look at next lines for time and UTR
            time_str = ""
            utr = ""
            txn_id = ""

            j = i + 1
            while j < len(lines) and j < i + 4:
                next_line = lines[j]

                # Time and Transaction ID
                time_match = time_txn_pattern.match(next_line)
                if time_match:
                    time_str = time_match.group(1)
                    txn_id = time_match.group(2)

                # UTR
                utr_match = utr_pattern.search(next_line)
                if utr_match:
                    utr = utr_match.group(1)

                # Stop if we hit next transaction
                if txn_line_pattern.match(next_line):
                    break

                j += 1

            transactions.append({
                "Date & Time": f"{date_str} {time_str}".strip(),
                "Transaction Details": merchant,
                "Notes & Tags": "",
                "Amount": amount,
                "UPI Ref": utr or txn_id
            })

            i = j
        else:
            i += 1

    if not transactions:
        st.warning(
            "Could not parse transactions from PhonePe PDF. "
            "Try Excel format if available."
        )
        return pd.DataFrame()

    df = pd.DataFrame(transactions)
    st.success(
        f"Successfully parsed {len(df)} "
        f"transactions from PhonePe PDF!"
    )
    return df