"""Procedure name to CPT code mapping."""
from __future__ import annotations

from typing import Any

from .claude import complete_json, is_configured
from .prompts import CPT_PROMPT_TEMPLATE

# Fallback table used when Claude is not configured. Keys are matched as
# substrings of the lower-cased query.
SAMPLE_CPT_TABLE: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("mri", "knee"), "73721", "MRI knee without contrast"),
    (("mri", "brain"), "70553", "MRI brain without and with contrast"),
    (("mri",), "70553", "MRI without and with contrast"),
    (("ct", "abdomen"), "74177", "CT abdomen and pelvis with contrast"),
    (("ct",), "74177", "CT with contrast"),
    (("colonoscopy",), "45378", "Diagnostic colonoscopy"),
    (("knee", "replacement"), "27447", "Total knee arthroplasty"),
    (("x-ray",), "73562", "X-ray knee, three views"),
    (("xray",), "73562", "X-ray knee, three views"),
    (("mammogram",), "77067", "Screening mammography, bilateral"),
    (("ultrasound",), "76700", "Ultrasound, abdominal, complete"),
    (("office", "visit"), "99214", "Office visit, established patient"),
)

# Used when nothing in the table matches.
DEFAULT_CPT = ("99214", "Office visit, established patient")


def _sample_lookup(procedure_name: str) -> dict[str, str]:
    query = (procedure_name or "").lower()

    for keywords, cpt_code, official_name in SAMPLE_CPT_TABLE:
        if all(keyword in query for keyword in keywords):
            return {"cpt_code": cpt_code, "procedure_name": official_name}

    cpt_code, official_name = DEFAULT_CPT
    return {"cpt_code": cpt_code, "procedure_name": official_name}


def map_procedure_to_cpt(procedure_name: str) -> tuple[dict[str, str], str]:
    """Map a free-text procedure description to a CPT code.

    Returns (mapping, source) where mapping has cpt_code and procedure_name.
    """
    if not is_configured():
        return _sample_lookup(procedure_name), "sample"

    parsed = complete_json(
        system="Return JSON only. No explanation.",
        content=[
            {
                "type": "text",
                "text": CPT_PROMPT_TEMPLATE.format(procedure_name=procedure_name),
            }
        ],
    )

    return (
        {
            "cpt_code": str(parsed.get("cpt_code") or "").strip(),
            "procedure_name": str(
                parsed.get("procedure_name") or procedure_name
            ).strip(),
        },
        "claude",
    )
