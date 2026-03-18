import pandas as pd
import streamlit as st
import plotly.express as px


def parse_date(date_str):
    import re
    date_str = str(date_str).strip()

    # Try standard formats first
    for fmt in ["%d/%m/%Y", "%d-%m-%Y",
                "%Y-%m-%d", "%d %b %Y"]:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            pass

    # Handle Paytm format "15 Mar" or "15 Mar 3:06 PM"
    match = re.match(
        r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|'
        r'Jul|Aug|Sep|Oct|Nov|Dec)',
        date_str, re.IGNORECASE
    )
    if match:
        day = match.group(1)
        month = match.group(2)
        year = pd.Timestamp.now().year
        try:
            return pd.to_datetime(
                f"{day} {month} {year}",
                format="%d %b %Y"
            )
        except:
            pass

    return pd.NaT


def show_analysis(df):

    # ── Find amount column ──
    amount_col = None
    for col in df.columns:
        if "amount" in str(col).lower():
            amount_col = col
            break

    if amount_col is None:
        st.error("Could not find Amount column.")
        return

    # ── Convert amount to numeric ──
    df[amount_col] = pd.to_numeric(
        df[amount_col], errors="coerce"
    ).fillna(0)

    # ── Split income and expenses ──
    income_df = df[df[amount_col] > 0]
    expense_df = df[df[amount_col] < 0]

    total_income = income_df[amount_col].sum()
    total_spent = abs(expense_df[amount_col].sum())
    net_savings = total_income - total_spent

    # ── Section 1 — Summary Cards ──
    st.markdown("### 💡 Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Income",
            value=f"₹{total_income:,.2f}"
        )
    with col2:
        st.metric(
            label="Total Spent",
            value=f"₹{total_spent:,.2f}"
        )
    with col3:
        st.metric(
            label="Net Savings",
            value=f"₹{net_savings:,.2f}",
            delta=f"{'Saved' if net_savings > 0 else 'Overspent'}"
        )

    st.markdown("---")

    # ── Section 2 — Spending by Category ──
    st.markdown("### 📊 Spending by Category")

    category_df = expense_df.groupby(
        "Category"
    )[amount_col].sum().abs()
    category_df = category_df.reset_index()
    category_df.columns = ["Category", "Amount"]
    category_df = category_df.sort_values(
        "Amount", ascending=False
    )

    fig_pie = px.pie(
        category_df,
        values="Amount",
        names="Category",
        hole=0.4
    )
    fig_pie.update_traces(
        textposition="outside",
        textinfo="percent+label",
        pull=[0.05] * len(category_df)
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.1
        ),
        margin=dict(t=40, b=40, l=40, r=160),
        hoverlabel=dict(
            bgcolor="rgba(0,0,0,0.8)",
            font_size=14
        )
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # ── Section 3 — Spending over Time ──
    st.markdown("### 📈 Spending over Time")

    date_col = None
    for col in df.columns:
        if "date" in str(col).lower():
            date_col = col
            break

    if date_col:
        expense_df = expense_df.copy()
        expense_df[date_col] = expense_df[date_col].apply(
            parse_date
        )
        expense_df = expense_df.dropna(subset=[date_col])

        daily_spend = expense_df.groupby(
            date_col
        )[amount_col].sum().abs().reset_index()
        daily_spend.columns = ["Date", "Amount Spent"]

        fig_line = px.line(
            daily_spend,
            x="Date",
            y="Amount Spent",
            markers=True
        )
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )
        st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")

    # ── Section 4 — Top 10 Transactions ──
    st.markdown("### 🔺 Top 10 Transactions")

    top10 = expense_df.nsmallest(
        10, amount_col
    )[[date_col, amount_col, "Category"]] if date_col else \
        expense_df.nsmallest(
            10, amount_col
        )[[amount_col, "Category"]]

    top10[amount_col] = top10[amount_col].abs()
    top10.columns = [
        col.replace(amount_col, "Amount")
        for col in top10.columns
    ]

    st.dataframe(top10, use_container_width=True)