"""Denial reason classification.

Maps a payer's denial reason code onto one of four categories. Deterministic
by design: an appeal's whole downstream path depends on this call, so it has
to be explainable rather than inferred.
"""
from __future__ import annotations

from typing import Literal

DenialCategory = Literal[
    "medical_necessity", "not_covered", "missing_info", "other"
]

# Exact reason codes seen from payers, checked before any keyword matching.
KNOWN_CODES: dict[str, DenialCategory] = {
    # Medical necessity
    "MN-001": "medical_necessity",
    "MN-002": "medical_necessity",
    "DN-MEDNEC": "medical_necessity",
    "50": "medical_necessity",  # X12 CARC 50: not deemed a medical necessity
    # Not covered
    "NC-001": "not_covered",
    "DN-NOTCOV": "not_covered",
    "96": "not_covered",  # X12 CARC 96: non-covered charge
    "204": "not_covered",  # X12 CARC 204: not covered under the plan
    # Missing information
    "MI-001": "missing_info",
    "DN-MISSINFO": "missing_info",
    "16": "missing_info",  # X12 CARC 16: lacks information
    "252": "missing_info",  # X12 CARC 252: attachment required
}

# Keyword fallback, checked in order. The first matching group wins, so more
# specific phrases must precede more general ones.
KEYWORD_RULES: tuple[tuple[DenialCategory, tuple[str, ...]], ...] = (
    (
        "missing_info",
        (
            "missing",
            "insufficient",
            "incomplete",
            "documentation",
            "additional information",
            "attachment",
            "records not received",
        ),
    ),
    (
        "not_covered",
        (
            "not covered",
            "non-covered",
            "noncovered",
            "excluded",
            "exclusion",
            "not a benefit",
            "benefit limitation",
            "plan does not cover",
        ),
    ),
    (
        "medical_necessity",
        (
            "medical necessity",
            "medically necessary",
            "not necessary",
            "experimental",
            "investigational",
            "criteria not met",
            "conservative treatment",
        ),
    ),
)


def classify_denial(denial_reason_code: str | None) -> DenialCategory:
    """Classify a denial reason code.

    Anything unrecognized becomes "other", which still routes to an appeal —
    only "not_covered" skips straight to a human.
    """
    raw = (denial_reason_code or "").strip()
    if not raw:
        return "other"

    exact = KNOWN_CODES.get(raw.upper())
    if exact is not None:
        return exact

    lowered = raw.lower()
    for category, keywords in KEYWORD_RULES:
        if any(keyword in lowered for keyword in keywords):
            return category

    return "other"
