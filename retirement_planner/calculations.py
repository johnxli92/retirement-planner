from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Dict, Any

import pandas as pd

# Use relative import for better compatibility with Streamlit Cloud
from .taxes import TaxInput, TaxResult, compute_taxes, estimate_brokerage_gains


WithdrawalOrder = Literal["brokerage_first", "tax_deferred_first"]


@dataclass
class ProjectionConfig:
    current_age: int
    retire_age: int
    end_age: int = 100

    current_401k_balance: float = 0.0
    current_brokerage_balance: float = 0.0

    annual_401k_contribution: float = 0.0
    annual_brokerage_contribution: float = 0.0

    real_return_401k: float = 0.05
    real_return_brokerage: float = 0.05

    swr: float = 0.04

    filing_status: str = "single"
    state_tax_rate: float = 0.05
    withdrawal_order: WithdrawalOrder = "brokerage_first"


def _year_sequence(config: ProjectionConfig) -> List[int]:
    return list(range(config.current_age, config.end_age + 1))


def run_projection(config: ProjectionConfig) -> pd.DataFrame:
    years = _year_sequence(config)

    balance_401k = config.current_401k_balance
    balance_brokerage = config.current_brokerage_balance

    rows: List[Dict[str, Any]] = []

    for age in years:
        year_index = age - config.current_age

        is_retirement_year = age >= config.retire_age

        pre_growth_401k = balance_401k
        pre_growth_brokerage = balance_brokerage

        if not is_retirement_year:
            pre_growth_401k += config.annual_401k_contribution
            pre_growth_brokerage += config.annual_brokerage_contribution

        post_growth_401k = pre_growth_401k * (1 + config.real_return_401k)
        post_growth_brokerage = pre_growth_brokerage * (1 + config.real_return_brokerage)

        withdrawal_total = 0.0
        withdrawal_401k = 0.0
        withdrawal_brokerage = 0.0
        
        # Social Security starts at age 62, maximum benefit at age 62 is ~$41,000/year
        # Only applies during retirement years
        # Apply COLA (Cost of Living Adjustment) - typically 2-3% per year
        SOCIAL_SECURITY_MAX_AGE_62 = 41000.0
        SOCIAL_SECURITY_COLA = 0.025  # 2.5% annual COLA adjustment
        
        if is_retirement_year and age >= 62:
            # Calculate years since age 62 for COLA compounding
            years_since_62 = age - 62
            social_security_income = SOCIAL_SECURITY_MAX_AGE_62 * ((1 + SOCIAL_SECURITY_COLA) ** years_since_62)
        else:
            social_security_income = 0.0

        tax_input: TaxInput | None = None
        tax_result: TaxResult | None = None

        if is_retirement_year:
            # Calculate withdrawal as percentage of current year's portfolio balance
            current_portfolio_balance = post_growth_401k + post_growth_brokerage
            withdrawal_total = current_portfolio_balance * config.swr

            if config.withdrawal_order == "brokerage_first":
                from_brokerage = min(withdrawal_total, post_growth_brokerage)
                from_401k = withdrawal_total - from_brokerage
            else:
                from_401k = min(withdrawal_total, post_growth_401k)
                from_brokerage = withdrawal_total - from_401k

            withdrawal_401k = from_401k
            withdrawal_brokerage = from_brokerage

            balance_401k = post_growth_401k - withdrawal_401k
            balance_brokerage = post_growth_brokerage - withdrawal_brokerage

            est_cap_gains = estimate_brokerage_gains(withdrawal_brokerage)

            tax_input = TaxInput(
                filing_status=config.filing_status,
                state_rate=config.state_tax_rate,
                ordinary_income=withdrawal_401k,
                capital_gains_income=est_cap_gains,
                social_security_income=social_security_income,
            )
            tax_result = compute_taxes(tax_input)
        else:
            balance_401k = post_growth_401k
            balance_brokerage = post_growth_brokerage

        total_balance = balance_401k + balance_brokerage

        total_tax = tax_result.total_tax if tax_result else 0.0
        # Net income includes both withdrawals and Social Security
        total_income = withdrawal_total + social_security_income
        net_income = total_income - total_tax

        row: Dict[str, Any] = {
            "age": age,
            "year_index": year_index,
            "is_retirement_year": is_retirement_year,
            "balance_401k": balance_401k,
            "balance_brokerage": balance_brokerage,
            "total_balance": total_balance,
            "withdrawal_total": withdrawal_total,
            "withdrawal_401k": withdrawal_401k,
            "withdrawal_brokerage": withdrawal_brokerage,
            "social_security_income": social_security_income,
            "tax_total": total_tax,
            "net_income_after_tax": net_income,
        }

        if tax_result is not None:
            row.update(
                {
                    "tax_effective_rate": tax_result.effective_rate,
                    "federal_tax": tax_result.federal_tax,
                    "state_tax": tax_result.state_tax,
                }
            )
        else:
            row.update(
                {
                    "tax_effective_rate": 0.0,
                    "federal_tax": 0.0,
                    "state_tax": 0.0,
                }
            )

        rows.append(row)

    df = pd.DataFrame(rows)
    return df


