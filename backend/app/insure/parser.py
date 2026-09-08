"""Insurance document parsing.

The card image goes to Claude with vision; the EOC PDF goes to Claude as a
document block. The two JSON results are merged into one insurance_plan.

Without an Anthropic API key the parsers return clearly-labelled sample data
so the flow stays demoable. Every parse result carries a `source` of "claude"
or "sample" so the caller — and the UI — can tell which produced it.
"""
from __future__ import annotations

import base64
from typing import Any, Optional

from .claude import (
    ClaudeResponseError,
    ClaudeUnavailableError,
    complete_json,
    is_configured,
)
from .prompts import (
    CARD_FIELDS,
    CARD_SYSTEM_PROMPT,
    EOC_FIELDS,
    EOC_SYSTEM_PROMPT,
)

# Media types accepted for the card image.
IMAGE_MEDIA_TYPES = {
    "image/jpeg": (".jpg", ".jpeg"),
    "image/png": (".png",),
}

# Stand-in values used when Claude is not configured. Deliberately obvious so
# nobody mistakes them for a real member's plan.
SAMPLE_CARD: dict[str, Any] = {
    "plan_name": "SAMPLE PPO 2000",
    "insurance_company": "SAMPLE Health Plan",
    "group_number": "SAMPLE-GRP-0001",
    "member_id": "SAMPLE-MBR-0001",
    "network_name": "SAMPLE Preferred Network",
}

SAMPLE_EOC: dict[str, Any] = {
    "deductible_individual": 2000.0,
    "deductible_family": 4000.0,
    "deductible_met": 0.0,
    "out_of_pocket_max_individual": 8000.0,
    "out_of_pocket_max_family": 16000.0,
    "primary_care_copay": 30.0,
    "specialist_copay": 60.0,
    "er_copay": 400.0,
    "coinsurance_percentage": 20.0,
    "covered_services": [
        "Preventive care",
        "Diagnostic imaging",
        "Outpatient surgery",
        "Emergency services",
    ],
    "prior_auth_required_for": [
        "Advanced imaging (MRI, CT, PET)",
        "Inpatient surgery",
    ],
}


def normalize_media_type(filename: str, content_type: Optional[str]) -> str:
    """Resolve a card image's media type, trusting the extension over a
    generic or missing content type."""
    lowered = (filename or "").lower()
    for media_type, extensions in IMAGE_MEDIA_TYPES.items():
        if lowered.endswith(extensions):
            return media_type

    if content_type in IMAGE_MEDIA_TYPES:
        return content_type

    raise ValueError(
        f"Unsupported card image type {content_type or filename!r}. "
        "Upload a JPG or PNG."
    )


def _fill_missing(parsed: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    """Ensure every expected field is present, defaulting to None."""
    return {field: parsed.get(field) for field in fields}


def parse_card(image_bytes: bytes, media_type: str) -> tuple[dict[str, Any], str]:
    """Extract plan identity from an insurance card image.

    Returns (fields, source).
    """
    if not is_configured():
        return dict(SAMPLE_CARD), "sample"

    parsed = complete_json(
        system=CARD_SYSTEM_PROMPT,
        content=[
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64.standard_b64encode(image_bytes).decode("ascii"),
                },
            },
            {"type": "text", "text": "Extract the fields from this insurance card."},
        ],
    )
    return _fill_missing(parsed, CARD_FIELDS), "claude"


def parse_eoc(pdf_bytes: bytes) -> tuple[dict[str, Any], str]:
    """Extract cost-sharing structure from an Evidence of Coverage PDF.

    Returns (fields, source).
    """
    if not is_configured():
        return dict(SAMPLE_EOC), "sample"

    parsed = complete_json(
        system=EOC_SYSTEM_PROMPT,
        content=[
            # The document block precedes the instruction text.
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.standard_b64encode(pdf_bytes).decode("ascii"),
                },
            },
            {
                "type": "text",
                "text": "Extract the fields from this Evidence of Coverage document.",
            },
        ],
    )
    return _fill_missing(parsed, EOC_FIELDS), "claude"


def merge_plan(
    card_fields: dict[str, Any], eoc_fields: dict[str, Any]
) -> dict[str, Any]:
    """Merge the card and EOC results into one insurance_plan object.

    The two field sets are disjoint, so neither can silently overwrite the
    other.
    """
    return {**card_fields, **eoc_fields}


def parse_documents(
    *,
    card_bytes: bytes,
    card_media_type: str,
    eoc_bytes: bytes,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Parse both documents and merge them.

    Returns (insurance_plan, sources) where sources names the parser used for
    each document.
    """
    card_fields, card_source = parse_card(card_bytes, card_media_type)
    eoc_fields, eoc_source = parse_eoc(eoc_bytes)

    return (
        merge_plan(card_fields, eoc_fields),
        {"card": card_source, "eoc": eoc_source},
    )
