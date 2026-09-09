"""Appeal letter generation."""
from __future__ import annotations

from typing import Any

from ..claude_client import complete_json, is_configured
from ..fhir import CPT_DISPLAY, ICD10_DISPLAY
from .prompts import APPEAL_LETTER_PROMPT
from .pubmed import format_citations


def summarize_fhir_bundle(fhir_bundle: dict[str, Any]) -> str:
    """Flatten a FHIR bundle into the clinical context line of the prompt."""
    if not fhir_bundle:
        return "No FHIR bundle was available for this request."

    lines: list[str] = []
    for entry in fhir_bundle.get("entry", []):
        resource = entry.get("resource", {})
        kind = resource.get("resourceType")

        if kind == "Patient":
            lines.append(f"Patient reference: {resource.get('id')} (identifier hashed)")
        elif kind == "Condition":
            code = resource.get("code", {})
            coding = (code.get("coding") or [{}])[0]
            lines.append(
                f"Condition: {code.get('text') or coding.get('display') or 'unspecified'}"
                f" (ICD-10 {coding.get('code')}), recorded {resource.get('recordedDate')}"
            )
        elif kind == "ServiceRequest":
            code = resource.get("code", {})
            coding = (code.get("coding") or [{}])[0]
            lines.append(
                f"Ordered procedure: {code.get('text') or coding.get('display') or 'unspecified'}"
                f" (CPT {coding.get('code')}), intent {resource.get('intent')},"
                f" priority {resource.get('priority')}, authored {resource.get('authoredOn')}"
            )

    return "\n".join(lines) if lines else "The FHIR bundle contained no clinical resources."


def _stub_letter(
    *,
    denial_reason_code: str,
    procedure_code: str,
    diagnosis_code: str,
    citations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Placeholder used when no Anthropic key is configured.

    Deliberately labelled as a draft so it can never be mistaken for a letter
    a clinician would sign, and scored below the submission threshold so it
    escalates to a human instead of being submitted automatically.
    """
    procedure_label = CPT_DISPLAY.get(procedure_code, f"CPT {procedure_code}")
    diagnosis_label = ICD10_DISPLAY.get(diagnosis_code, f"ICD-10 {diagnosis_code}")
    pmids = ", ".join(
        f"PMID {citation['pmid']}" for citation in citations if citation.get("pmid")
    )

    letter = (
        "SAMPLE DRAFT — generated without a language model.\n\n"
        "Attention: Medical Director\n\n"
        f"We are appealing the denial issued under reason code {denial_reason_code} "
        f"for {procedure_label} in a patient with {diagnosis_label}.\n\n"
        "This placeholder stands in for the drafted appeal. Set ANTHROPIC_API_KEY "
        "to generate a letter from the patient's clinical context and the "
        "retrieved literature.\n\n"
        + (f"Retrieved evidence: {pmids}.\n\n" if pmids else "")
        + "Expedited review is requested."
    )

    return {
        "letter": letter,
        # Below the submission threshold on purpose: a placeholder must never
        # be submitted to a payer without a human reading it.
        "confidence": 0.0,
        "key_arguments": [
            "Placeholder draft; no clinical argument has been generated.",
            "Configure ANTHROPIC_API_KEY to draft a real appeal.",
        ],
    }


def generate_appeal_letter(
    *,
    denial_reason_code: str,
    procedure_code: str,
    diagnosis_code: str,
    fhir_bundle: dict[str, Any],
    citations: list[dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    """Draft an appeal letter.

    Returns (result, source) where result carries letter, confidence, and
    key_arguments, and source is "claude" or "sample".
    """
    if not is_configured():
        return (
            _stub_letter(
                denial_reason_code=denial_reason_code,
                procedure_code=procedure_code,
                diagnosis_code=diagnosis_code,
                citations=citations,
            ),
            "sample",
        )

    prompt = APPEAL_LETTER_PROMPT.format(
        denial_reason_code=denial_reason_code,
        procedure_code=procedure_code,
        diagnosis_code=diagnosis_code,
        fhir_bundle_summary=summarize_fhir_bundle(fhir_bundle),
        pubmed_citations=format_citations(citations),
    )

    parsed = complete_json(
        system="Return JSON only. No explanation.",
        content=[{"type": "text", "text": prompt}],
    )

    raw_confidence = parsed.get("confidence")
    try:
        confidence = float(raw_confidence)
    except (TypeError, ValueError):
        # An unreadable score must not read as high confidence.
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    arguments = parsed.get("key_arguments")
    if not isinstance(arguments, list):
        arguments = []

    return (
        {
            "letter": str(parsed.get("letter") or "").strip(),
            "confidence": confidence,
            "key_arguments": [str(argument) for argument in arguments],
        },
        "claude",
    )
