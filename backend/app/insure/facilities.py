"""Mock facility pricing.

Phase 2 stands in for the Vapi voice agent that will call facilities for live
rates. Prices are generated deterministically from the CPT code so a given
procedure always returns the same five facilities — repeatable demos, and a
stable fixture for tests.

Cash prices land 60-80% below the negotiated rate. That gap is the product's
central insight: for a member who has not met their deductible, paying cash
is frequently cheaper than using their insurance.
"""
from __future__ import annotations

import random
from typing import Any

# Five fixed facilities. Only their prices vary by procedure.
FACILITIES: tuple[dict[str, Any], ...] = (
    {
        "facility_id": "fac-001",
        "name": "Metro Valley Medical Center",
        "type": "Hospital",
        "city": "Springfield",
    },
    {
        "facility_id": "fac-002",
        "name": "Riverside Imaging & Surgical",
        "type": "Outpatient center",
        "city": "Springfield",
    },
    {
        "facility_id": "fac-003",
        "name": "Northgate Community Hospital",
        "type": "Hospital",
        "city": "Northgate",
    },
    {
        "facility_id": "fac-004",
        "name": "Clearview Ambulatory Care",
        "type": "Ambulatory surgery center",
        "city": "Clearview",
    },
    {
        "facility_id": "fac-005",
        "name": "Parkside Diagnostic Clinic",
        "type": "Independent clinic",
        "city": "Parkside",
    },
)

# Typical negotiated rate by CPT range. Ranges are checked in order.
CPT_PRICE_BANDS: tuple[tuple[int, int, float], ...] = (
    (70000, 70999, 2400.0),   # MRI / advanced neuro imaging
    (71000, 73599, 450.0),    # Plain-film radiography
    (73600, 74999, 1900.0),   # CT and MSK MRI
    (75000, 76999, 700.0),    # Ultrasound and vascular imaging
    (77000, 79999, 380.0),    # Mammography and radiation oncology
    (10000, 29999, 32000.0),  # Musculoskeletal surgery
    (30000, 49999, 2600.0),   # Endoscopy and general surgery
    (50000, 69999, 5200.0),   # Urologic, ocular, and other surgery
    (90000, 99999, 220.0),    # Evaluation and management
)

# Used when a CPT code falls outside every band, or is not numeric.
DEFAULT_BASE_RATE = 1200.0


def base_rate_for_cpt(cpt_code: str) -> float:
    """Typical negotiated rate for the band this CPT code falls in."""
    digits = "".join(character for character in (cpt_code or "") if character.isdigit())
    if not digits:
        return DEFAULT_BASE_RATE

    numeric = int(digits[:5])
    for low, high, rate in CPT_PRICE_BANDS:
        if low <= numeric <= high:
            return rate

    return DEFAULT_BASE_RATE


def get_facility_pricing(cpt_code: str) -> list[dict[str, Any]]:
    """Return the five facilities priced for this CPT code.

    Seeded by the CPT code, so the same procedure always yields the same
    quotes.
    """
    base_rate = base_rate_for_cpt(cpt_code)
    rng = random.Random(f"pavo-insure::{cpt_code}")

    priced: list[dict[str, Any]] = []
    for facility in FACILITIES:
        # Facilities negotiate quite differently for the same procedure.
        negotiated_rate = round(base_rate * rng.uniform(0.7, 1.45), 2)

        # Cash prices run 60-80% below the negotiated rate.
        cash_discount = rng.uniform(0.60, 0.80)
        cash_price = round(negotiated_rate * (1 - cash_discount), 2)

        priced.append(
            {
                **facility,
                "negotiated_rate": negotiated_rate,
                "cash_price": cash_price,
                "cash_discount_percentage": round(cash_discount * 100, 1),
                "quality_score": rng.randint(1, 5),
                "distance_miles": round(rng.uniform(1.2, 24.0), 1),
            }
        )

    return priced
