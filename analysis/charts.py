import pandas as pd
import streamlit as st
import plotly.express as px


def parse_date(date_str):
    import re
    date_str = str(date_str).strip()

    # Handle already parsed datetime objects
    if "00:00:00" in date_str:
        try:
            return pd.to_datetime(date_str)
        except:
            pass

    # Try standard formats
    for fmt in [
        "%d/%m/%Y", "%d-%m-%Y",
        "%Y-%m-%d", "%d %b %Y",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S"
    ]:
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

    # Last resort — let pandas figure it out
    try:
        return pd.to_datetime(date_str, infer_datetime_format=True)
    except:
        pass

    return pd.NaT

def show_category_trends(expense_df, amount_col, date_col):
    st.markdown("### 📊 Category Spending Trends")
    st.caption("See how your spending in each category changes week by week.")

    # Parse dates
    trend_df = expense_df.copy()
    trend_df[date_col] = trend_df[date_col].apply(parse_date)
    trend_df = trend_df.dropna(subset=[date_col])

    if trend_df.empty:
        st.warning("Not enough date data for trends.")
        return

    # Add week column
    trend_df["Week"] = trend_df[date_col].dt.to_period("W").apply(
        lambda r: r.start_time
    )

    # Group by week and category
    weekly = trend_df.groupby(
        ["Week", "Category"]
    )[amount_col].sum().abs().reset_index()
    weekly.columns = ["Week", "Category", "Amount"]

    # Only show top 5 categories by total spend
    # Too many lines makes chart unreadable
    top_categories = weekly.groupby(
        "Category"
    )["Amount"].sum().nlargest(5).index.tolist()

    weekly = weekly[weekly["Category"].isin(top_categories)]

    fig_trend = px.line(
        weekly,
        x="Week",
        y="Amount",
        color="Category",
        markers=True,
        labels={
            "Week": "Week",
            "Amount": "Amount Spent (₹)",
            "Category": "Category"
        }
    )
    fig_trend.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=13)
        ),
        margin=dict(t=40, b=40, l=40, r=200),
        hoverlabel=dict(
            bgcolor="rgba(0,0,0,0.8)",
            font_size=14
        ),
        hovermode="x unified"
    )
    fig_trend.update_traces(line=dict(width=2))
    st.plotly_chart(fig_trend, use_container_width=True)

def show_analysis(df, budget=0):

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

    # ── Only look at expenses — ignore all incoming ──
    expense_df = df[df[amount_col] < 0]
    total_spent = abs(expense_df[amount_col].sum())

    # Budget calculations
    if budget > 0:
        budget_remaining = budget - total_spent
        budget_used_pct = (total_spent / budget * 100)

    # ── Section 1 — Summary Cards ──
    st.markdown("### 💡 Summary")

    if budget > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="Monthly Budget",
                value=f"₹{budget:,.0f}"
            )
        with col2:
            st.metric(
                label="Total Spent",
                value=f"₹{total_spent:,.2f}",
                delta=f"{budget_used_pct:.1f}% of budget used",
                delta_color="inverse"
            )
        with col3:
            st.metric(
                label="Budget Remaining",
                value=f"₹{budget_remaining:,.2f}",
                delta=f"{'On track' if budget_remaining > 0 else 'Over budget'}",
                delta_color="normal" if budget_remaining > 0 else "inverse"
            )
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Total Spent",
                value=f"₹{total_spent:,.2f}"
            )
        with col2:
            st.metric(
                label="Transactions",
                value=f"{len(expense_df)}"
            )

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

    # Add percentage to category names for legend
    total = category_df["Amount"].sum()
    category_df["Label"] = category_df.apply(
        lambda row: f"{row['Category']} ({row['Amount']/total*100:.1f}%)",
        axis=1
    )

    fig_pie = px.pie(
        category_df,
        values="Amount",
        names="Label",
        hole=0.4
    )
    fig_pie.update_traces(
        textposition="inside",
        textinfo="percent",
        pull=[0.05] * len(category_df),
        insidetextfont=dict(size=10)
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
            x=1.05,
            font=dict(size=14)
        ),
        margin=dict(t=40, b=40, l=40, r=200),
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

    st.markdown("---")

    # ── Section 4 — Category Trends ──
    if date_col and "Category" in expense_df.columns:
        show_category_trends(expense_df, amount_col, date_col)
        st.markdown("---")

    # ── Section 5 — Top 10 Transactions ──
    st.markdown("### 🔺 Top 10 Transactions")

    top10 = expense_df.nsmallest(
        10, amount_col
    )[[date_col, amount_col, "Category"]] if date_col else \
        expense_df.nsmallest(
            10, amount_col
        )[[amount_col, "Category"]]

    top10[amount_col] = top10[amount_col].abs()

    # Clean date format for display
    if date_col in top10.columns:
        top10[date_col] = pd.to_datetime(
            top10[date_col], errors="coerce"
        ).dt.strftime("%d %b %Y")

    top10.columns = [
        col.replace(amount_col, "Amount")
        for col in top10.columns
    ]

    st.dataframe(top10, use_container_width=True)