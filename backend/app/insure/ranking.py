"""Ranking algorithm.

Turns facility quotes into a list ordered by what the member actually pays.

The two payment formulas come from the Phase 2 specification:

    deductible not met -> min(cash_price, coinsurance x negotiated_rate)
    deductible met     -> coinsurance x negotiated_rate

Note that these apply coinsurance whether or not the deductible is met, which
is not how a real plan behaves — before the deductible is met a member
normally owes the full negotiated rate, and coinsurance starts afterwards.
The specification's formulas are implemented verbatim here; changing them is a
product decision, and the one place to make it is `estimate_member_cost`.
"""
from __future__ import annotations

from typing import Any, Optional

# Assumed when the EOC gives no coinsurance percentage.
DEFAULT_COINSURANCE_PERCENTAGE = 20.0


def _as_float(value: Any) -> Optional[float]:
    """Coerce a parsed plan value to a float.

    EOC parsing can yield numbers, numeric strings, or currency-formatted
    strings, so strip formatting before converting.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    cleaned = str(value).strip().replace("$", "").replace(",", "").replace("%", "")
    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def coinsurance_rate(insurance_plan: dict[str, Any]) -> float:
    """Member's coinsurance share as a fraction (20% -> 0.2)."""
    percentage = _as_float(insurance_plan.get("coinsurance_percentage"))
    if percentage is None:
        percentage = DEFAULT_COINSURANCE_PERCENTAGE

    # Tolerate a plan that expresses coinsurance as a fraction already.
    if 0 < percentage <= 1:
        return percentage

    return percentage / 100.0


def is_deductible_met(insurance_plan: dict[str, Any]) -> bool:
    """Whether the member has met their individual deductible.

    Unknown values are treated as not met, which is the conservative reading:
    it keeps the cash-price comparison in play rather than hiding it.
    """
    deductible = _as_float(insurance_plan.get("deductible_individual"))
    met = _as_float(insurance_plan.get("deductible_met"))

    if deductible is None or met is None:
        return False

    return met >= deductible


def estimate_member_cost(
    *,
    negotiated_rate: float,
    cash_price: float,
    coinsurance: float,
    deductible_met: bool,
) -> tuple[float, str, dict[str, Any]]:
    """What the member pays at one facility.

    Returns (amount, payment_method, breakdown) where payment_method is
    "insurance" or "cash".
    """
    insurance_cost = round(coinsurance * negotiated_rate, 2)

    if deductible_met:
        return (
            insurance_cost,
            "insurance",
            {
                "rule": "deductible_met",
                "formula": "coinsurance x negotiated_rate",
                "calculation": (
                    f"{coinsurance:.2f} x ${negotiated_rate:,.2f} = ${insurance_cost:,.2f}"
                ),
                "insurance_cost": insurance_cost,
                "cash_cost": cash_price,
            },
        )

    # Deductible not met: the member may do better paying cash.
    amount = min(cash_price, insurance_cost)
    method = "cash" if cash_price < insurance_cost else "insurance"

    return (
        amount,
        method,
        {
            "rule": "deductible_not_met",
            "formula": "min(cash_price, coinsurance x negotiated_rate)",
            "calculation": (
                f"min(${cash_price:,.2f}, {coinsurance:.2f} x ${negotiated_rate:,.2f}"
                f" = ${insurance_cost:,.2f}) = ${amount:,.2f}"
            ),
            "insurance_cost": insurance_cost,
            "cash_cost": cash_price,
        },
    )


def rank_facilities(
    facilities: list[dict[str, Any]],
    insurance_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    """Rank facilities by what the member actually pays, cheapest first."""
    coinsurance = coinsurance_rate(insurance_plan)
    deductible_met = is_deductible_met(insurance_plan)

    ranked: list[dict[str, Any]] = []
    for facility in facilities:
        negotiated_rate = float(facility["negotiated_rate"])
        cash_price = float(facility["cash_price"])

        amount, method, breakdown = estimate_member_cost(
            negotiated_rate=negotiated_rate,
            cash_price=cash_price,
            coinsurance=coinsurance,
            deductible_met=deductible_met,
        )

        ranked.append(
            {
                **facility,
                "you_pay": amount,
                "payment_method": method,
                "cheaper_option": method,
                "savings_vs_alternative": round(
                    abs(breakdown["insurance_cost"] - breakdown["cash_cost"]), 2
                ),
                "breakdown": {
                    **breakdown,
                    "coinsurance_rate": coinsurance,
                    "deductible_met": deductible_met,
                    "negotiated_rate": negotiated_rate,
                },
            }
        )

    ranked.sort(key=lambda item: (item["you_pay"], item["distance_miles"]))

    for position, facility in enumerate(ranked, start=1):
        facility["rank"] = position

    return ranked
