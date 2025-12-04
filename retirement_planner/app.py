from __future__ import annotations

import sys
import os

# Add parent directory to path for Streamlit Cloud deployment
# This ensures the retirement_planner package can be imported
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd

from retirement_planner.calculations import ProjectionConfig, run_projection


def _default_config() -> ProjectionConfig:
    return ProjectionConfig(
        current_age=51,
        retire_age=55,
        end_age=100,
        current_401k_balance=300000.0,
        current_brokerage_balance=600000.0,
        annual_401k_contribution=22000.0,
        annual_brokerage_contribution=12000.0,
        real_return_401k=0.07,
        real_return_brokerage=0.07,
        swr=0.04,
        filing_status="married",
        state_tax_rate=0.05,
        withdrawal_order="tax_deferred_first",
        social_security_start_age=62,
    )


def _build_sidebar(config: ProjectionConfig) -> ProjectionConfig:
    st.sidebar.header("Inputs")

    current_age = st.sidebar.number_input("Current age", min_value=18, max_value=90, value=config.current_age)
    retire_age = st.sidebar.number_input("Desired retirement age", min_value=current_age, max_value=95, value=config.retire_age)
    end_age = st.sidebar.number_input("Plan until age", min_value=retire_age, max_value=110, value=config.end_age)

    st.sidebar.subheader("Current balances")
    current_401k_balance = st.sidebar.number_input("401k balance", min_value=0.0, value=config.current_401k_balance, step=1000.0)
    current_brokerage_balance = st.sidebar.number_input("Brokerage balance", min_value=0.0, value=config.current_brokerage_balance, step=1000.0)

    st.sidebar.subheader("Annual contributions (until retirement)")
    annual_401k_contribution = st.sidebar.number_input("Annual 401k contribution", min_value=0.0, value=config.annual_401k_contribution, step=1000.0)
    annual_brokerage_contribution = st.sidebar.number_input("Annual brokerage contribution", min_value=0.0, value=config.annual_brokerage_contribution, step=1000.0)

    st.sidebar.subheader("Expected real returns")
    real_return_401k = st.sidebar.slider("401k real return (%)", min_value=-5.0, max_value=15.0, value=config.real_return_401k * 100, step=0.5) / 100.0
    real_return_brokerage = st.sidebar.slider("Brokerage real return (%)", min_value=-5.0, max_value=15.0, value=config.real_return_brokerage * 100, step=0.5) / 100.0

    st.sidebar.subheader("Withdrawal")
    swr_percent = st.sidebar.slider("Safe withdrawal rate (%)", min_value=2.0, max_value=6.0, value=config.swr * 100, step=0.25)
    swr = swr_percent / 100.0

    withdrawal_order = st.sidebar.selectbox(
        "Withdrawal order",
        options=["brokerage_first", "tax_deferred_first"],
        index=0 if config.withdrawal_order == "brokerage_first" else 1,
        format_func=lambda x: "Brokerage first, then 401k" if x == "brokerage_first" else "401k first, then brokerage",
    )

    st.sidebar.subheader("Taxes")
    filing_status = st.sidebar.selectbox("Filing status", options=["single", "married"], index=0 if config.filing_status == "single" else 1)
    state_tax_rate = st.sidebar.slider("State tax rate (%)", min_value=0.0, max_value=15.0, value=config.state_tax_rate * 100, step=0.5) / 100.0

    st.sidebar.subheader("Social Security")
    social_security_start_age = st.sidebar.slider("Social Security start age", min_value=62, max_value=70, value=config.social_security_start_age, step=1)

    return ProjectionConfig(
        current_age=int(current_age),
        retire_age=int(retire_age),
        end_age=int(end_age),
        current_401k_balance=float(current_401k_balance),
        current_brokerage_balance=float(current_brokerage_balance),
        annual_401k_contribution=float(annual_401k_contribution),
        annual_brokerage_contribution=float(annual_brokerage_contribution),
        real_return_401k=float(real_return_401k),
        real_return_brokerage=float(real_return_brokerage),
        swr=float(swr),
        filing_status=filing_status,
        state_tax_rate=float(state_tax_rate),
        withdrawal_order=withdrawal_order,
        social_security_start_age=int(social_security_start_age),
    )


def _format_currency(value: float) -> str:
    """Format a float as USD currency without decimals."""
    return f"${value:,.0f}"


def _format_dataframe_currency(df: pd.DataFrame, currency_cols: list[str]) -> pd.DataFrame:
    """Format currency columns in a dataframe for display."""
    df_formatted = df.copy()
    for col in currency_cols:
        if col in df_formatted.columns:
            df_formatted[col] = df_formatted[col].apply(_format_currency)
    return df_formatted


def main() -> None:
    st.set_page_config(page_title="Retirement Planner", layout="wide")
    st.title("Retirement Planner")
    st.markdown(
        "Enter your information on the left to project your balances and retirement income. "
        "This is a simplified model and not tax or investment advice."
    )

    base_config = _default_config()
    config = _build_sidebar(base_config)

    df = run_projection(config)

    # Age selector slider in main window
    st.markdown("### Select Age to View Projections")
    selected_age = st.slider(
        "Age",
        min_value=config.current_age,
        max_value=config.end_age,
        value=config.retire_age,
        step=1,
        key="age_selector"
    )
    
    # Get row for selected age
    selected_row = df[df["age"] == selected_age].iloc[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Portfolio Balance", _format_currency(selected_row['total_balance']))
    with col2:
        st.metric("Annual withdrawal (pre-tax)", _format_currency(selected_row['withdrawal_total']))
    with col3:
        st.metric("Annual income (after tax)", _format_currency(selected_row['net_income_after_tax']))

    st.markdown("### Portfolio balances by age")
    balance_chart_df = df[["age", "balance_401k", "balance_brokerage", "total_balance"]].set_index("age")
    st.line_chart(balance_chart_df)

    st.markdown("### Withdrawals and taxes (retirement years)")
    retirement_df = df[df["is_retirement_year"]].copy()
    if not retirement_df.empty:
        display_cols = [
            "age",
            "withdrawal_total",
            "social_security_income",
            "tax_total",
            "net_income_after_tax",
            "tax_effective_rate",
            "balance_401k",
            "balance_brokerage",
            "total_balance",
        ]
        currency_cols = [
            "withdrawal_total",
            "social_security_income",
            "tax_total",
            "net_income_after_tax",
            "balance_401k",
            "balance_brokerage",
            "total_balance",
        ]
        display_df = retirement_df[display_cols].reset_index(drop=True)
        display_df_formatted = _format_dataframe_currency(display_df, currency_cols)
        st.dataframe(display_df_formatted)

        st.markdown("#### Annual withdrawal vs. after-tax income")
        income_chart_df = retirement_df[["age", "withdrawal_total", "net_income_after_tax"]].set_index("age")
        st.line_chart(income_chart_df)
    else:
        st.info("You have not reached retirement age within the planned horizon.")

    st.markdown("### Full projection")
    full_currency_cols = [
        "balance_401k",
        "balance_brokerage",
        "total_balance",
        "withdrawal_total",
        "withdrawal_401k",
        "withdrawal_brokerage",
        "social_security_income",
        "tax_total",
        "net_income_after_tax",
        "federal_tax",
        "state_tax",
    ]
    full_df_formatted = _format_dataframe_currency(df, full_currency_cols)
    st.dataframe(full_df_formatted)


if __name__ == "__main__":
    main()


