import pandas as pd
import streamlit as st


def clean_amount(val):
    if pd.isna(val):
        return 0
    cleaned = str(val).replace(",", "").replace(" ", "").strip()
    try:
        return float(cleaned)
    except:
        return 0


def make_columns_unique(columns):
    seen = {}
    new_columns = []
    for col in columns:
        if col in seen:
            seen[col] += 1
            new_columns.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_columns.append(col)
    return new_columns


def merge_debit_credit(df):
    withdrawal_col = None
    deposit_col = None

    for col in df.columns:
        if "withdrawal" in str(col).lower():
            withdrawal_col = col
        if "deposit" in str(col).lower():
            deposit_col = col

    if withdrawal_col is None or deposit_col is None:
        return df

    df["Amount"] = df.apply(
        lambda row: -clean_amount(row[withdrawal_col])
        if clean_amount(row[withdrawal_col]) != 0
        else clean_amount(row[deposit_col]),
        axis=1
    )

    df = df.drop(columns=[withdrawal_col, deposit_col])
    return df


def clean_excel_data(df):
    # Find real header row
    header_row_index = None

    for i, row in df.iterrows():
        for cell in row:
            if "date" in str(cell).lower():
                header_row_index = i
                break
        if header_row_index is not None:
            break

    if header_row_index is None:
        st.warning("Could not detect header row. Showing raw data.")
        return df

    # Set header row as column names
    df.columns = df.iloc[header_row_index]

    # Remove everything above and including header row
    df = df.iloc[header_row_index + 1:]

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Reset index
    df = df.reset_index(drop=True)

    # Clean column names
    df.columns = [
        str(col).strip().replace("\n", " ")
        for col in df.columns
    ]

    # Remove nan columns
    df = df.loc[:, df.columns.notna()]
    df = df.loc[:, df.columns != ""]
    df = df.loc[:, df.columns != "nan"]

    # Make duplicate column names unique
    df.columns = make_columns_unique(list(df.columns))

    # Remove columns that are completely empty
    df = df.dropna(axis=1, how="all")

    # Detect BOB style
    col_names_lower = [col.lower() for col in df.columns]
    has_withdrawal = any(
        "withdrawal" in col for col in col_names_lower
    )
    has_deposit = any(
        "deposit" in col for col in col_names_lower
    )

    if has_withdrawal and has_deposit:
        df = merge_debit_credit(df)

    # Remove rows where date column is None
    date_col = df.columns[0]
    df = df[df[date_col].notna()]
    df = df[df[date_col] != "None"]
    df = df.reset_index(drop=True)

    return df