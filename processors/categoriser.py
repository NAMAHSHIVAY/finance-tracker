import pandas as pd
import streamlit as st


def categorise_transaction(narration, amount, tags=None):

    # First check — if money coming IN it is always Income
    try:
        if float(amount) > 0:
            return "Income"
    except:
        pass

    # If tags column exists use it directly
    if tags and str(tags) != "nan" and str(tags).strip() != "":
        tag = str(tags).strip()
        tag = tag.replace("#", "").strip()
        tag = ''.join(char for char in tag
                      if char.isalnum()
                      or char.isspace()).strip()
        for bank_word in ["Baroda", "HDFC", "SBI", "Axis",
                          "Kotak", "ICICI", "PNB", "Bank"]:
            tag = tag.replace(bank_word, "").strip()
        if tag:
            return tag

    # For other banks extract from narration string
    narration = str(narration).lower()

    # Food and dining
    if any(word in narration for word in [
        "zomato", "swiggy", "food", "restaurant",
        "cafe", "hotel", "kitchen", "bakery",
        "dairy", "sweet", "dhaba"
    ]):
        return "Food"

    # Groceries
    if any(word in narration for word in [
        "grocer", "grocery", "bigbasket", "blinkit",
        "zepto", "dmart", "supermart", "vegetables",
        "fruits", "kirana"
    ]):
        return "Groceries"

    # Bills and utilities
    if any(word in narration for word in [
        "airtel", "jio", "bsnl", "vodafone", "vi",
        "electricity", "water", "gas", "bill",
        "recharge", "postpaid", "broadband", "internet"
    ]):
        return "Bills"

    # Shopping
    if any(word in narration for word in [
        "amazon", "flipkart", "myntra", "ajio",
        "meesho", "nykaa", "shopping", "mall",
        "store", "market"
    ]):
        return "Shopping"

    # Transport
    if any(word in narration for word in [
        "uber", "ola", "rapido", "metro", "irctc",
        "railway", "bus", "fuel", "petrol", "diesel",
        "parking", "fastag", "toll"
    ]):
        return "Transport"

    # Health and medical
    if any(word in narration for word in [
        "medical", "medicine", "pharma", "hospital",
        "clinic", "doctor", "health", "apollo",
        "netmeds", "1mg", "pharmacy"
    ]):
        return "Medical"

    # Entertainment
    if any(word in narration for word in [
        "netflix", "spotify", "prime", "hotstar",
        "youtube", "gaming", "movie", "cinema",
        "pvr", "inox", "adobe", "subscription"
    ]):
        return "Entertainment"

    # EMI and investments
    if any(word in narration for word in [
        "ach", "nach", "emi", "loan", "insurance",
        "mutual", "fund", "sip", "zerodha", "groww",
        "investment", "chola", "bajaj", "hdfc life"
    ]):
        return "EMI / Investment"

    # Income
    if any(word in narration for word in [
        "salary", "credit", "cashback", "refund",
        "interest", "dividend", "received", "upi/cr",
        "achcr", "neft/cr", "imps/cr"
    ]):
        return "Income"

    # Money transfers
    if any(word in narration for word in [
        "upi/dr", "neft", "imps", "transfer",
        "sent", "send", "payment"
    ]):
        return "Money Transfer"

    return "Other"


def add_categories(df):
    narration_col = None
    tags_col = None

    for col in df.columns:
        col_lower = str(col).lower()
        if any(word in col_lower for word in [
            "narration", "description", "details",
            "particular", "remarks", "transaction"
        ]):
            narration_col = col
        if "tag" in col_lower:
            tags_col = col

    if narration_col is None:
        st.warning("Could not detect narration column.")
        return df

    if tags_col:
        df["Category"] = df.apply(
            lambda row: categorise_transaction(
                row[narration_col],
                row["Amount"],
                row[tags_col]
            ),
            axis=1
        )
    else:
        df["Category"] = df.apply(
            lambda row: categorise_transaction(
                row[narration_col],
                row["Amount"]
            ),
            axis=1
        )

    return df