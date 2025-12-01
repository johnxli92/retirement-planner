from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


OrdinaryBracket = Tuple[float, float]  # (threshold, rate)


FEDERAL_BRACKETS_SINGLE: List[OrdinaryBracket] = [
    (0.0, 0.10),
    (11600.0, 0.12),
    (47150.0, 0.22),
    (100525.0, 0.24),
    (191950.0, 0.32),
    (243725.0, 0.35),
    (609350.0, 0.37),
]

FEDERAL_BRACKETS_MARRIED: List[OrdinaryBracket] = [
    (0.0, 0.10),
    (23200.0, 0.12),
    (94300.0, 0.22),
    (201050.0, 0.24),
    (383900.0, 0.32),
    (487450.0, 0.35),
    (731200.0, 0.37),
]

STANDARD_DEDUCTION = {
    "single": 14600.0,
    "married": 29200.0,
}


@dataclass
class TaxInput:
    filing_status: str  # "single" or "married"
    state_rate: float  # e.g. 0.05 for 5%
    ordinary_income: float  # 401k withdrawals + other ordinary
    capital_gains_income: float  # taxable gains from brokerage


@dataclass
class TaxResult:
    total_tax: float
    effective_rate: float
    federal_tax: float
    state_tax: float
    ordinary_income_taxed: float
    capital_gains_taxed: float


def _get_brackets(filing_status: str) -> List[OrdinaryBracket]:
    if filing_status == "married":
        return FEDERAL_BRACKETS_MARRIED
    return FEDERAL_BRACKETS_SINGLE


def _apply_ordinary_brackets(taxable_income: float, brackets: List[OrdinaryBracket]) -> float:
    if taxable_income <= 0:
        return 0.0

    tax = 0.0
    for i, (threshold, rate) in enumerate(brackets):
        if i + 1 < len(brackets):
            next_threshold = brackets[i + 1][0]
            amount_in_bracket = max(0.0, min(taxable_income, next_threshold) - threshold)
        else:
            amount_in_bracket = max(0.0, taxable_income - threshold)

        if amount_in_bracket <= 0:
            continue
        tax += amount_in_bracket * rate
    return tax


def compute_taxes(ti: TaxInput) -> TaxResult:
    filing_status = ti.filing_status if ti.filing_status in ("single", "married") else "single"
    brackets = _get_brackets(filing_status)

    std_deduction = STANDARD_DEDUCTION.get(filing_status, STANDARD_DEDUCTION["single"])

    taxable_ordinary = max(0.0, ti.ordinary_income - std_deduction)

    federal_ordinary_tax = _apply_ordinary_brackets(taxable_ordinary, brackets)

    capital_gains_rate = 0.15
    federal_capital_tax = max(0.0, ti.capital_gains_income) * capital_gains_rate

    federal_tax = federal_ordinary_tax + federal_capital_tax

    total_income = ti.ordinary_income + ti.capital_gains_income
    state_tax = max(0.0, total_income) * max(0.0, ti.state_rate)

    total_tax = federal_tax + state_tax
    effective_rate = total_tax / total_income if total_income > 0 else 0.0

    return TaxResult(
        total_tax=total_tax,
        effective_rate=effective_rate,
        federal_tax=federal_tax,
        state_tax=state_tax,
        ordinary_income_taxed=taxable_ordinary,
        capital_gains_taxed=ti.capital_gains_income,
    )


def estimate_brokerage_gains(withdrawal: float, gain_fraction: float = 0.5) -> float:
    if withdrawal <= 0:
        return 0.0
    gain_fraction = max(0.0, min(1.0, gain_fraction))
    return withdrawal * gain_fraction


