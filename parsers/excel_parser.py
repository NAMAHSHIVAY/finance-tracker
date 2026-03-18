import pandas as pd
import streamlit as st


def parse_excel(file):
    xl = pd.ExcelFile(file)
    sheet_names = xl.sheet_names

    # Step 1 — try keyword matching first
    transaction_keywords = [
        "transaction", "passbook", "history",
        "statement", "txn", "payment", "ledger"
    ]

    selected_sheet = None

    for sheet in sheet_names:
        for keyword in transaction_keywords:
            if keyword.lower() in sheet.lower():
                selected_sheet = sheet
                break
        if selected_sheet:
            break

    # Step 2 — fallback to most rows
    if selected_sheet is None:
        max_rows = 0
        selected_sheet = sheet_names[0]
        for sheet in sheet_names:
            temp_df = pd.read_excel(file, sheet_name=sheet)
            if len(temp_df) > max_rows:
                max_rows = len(temp_df)
                selected_sheet = sheet

    st.info(f"Auto detected transactions sheet: **{selected_sheet}**")
    df = pd.read_excel(file, sheet_name=selected_sheet)
    return df