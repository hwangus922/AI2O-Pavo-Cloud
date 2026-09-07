"""Deterministic rule engine.

Phase 1 hardcodes five coverage rules. Every evaluation returns a Decision
carrying the rule_id that produced it — there are no black box outputs.

Rules are evaluated in order and the first match wins, so the more specific
rule for a procedure must be declared before the catch-all for that same
procedure (27447 + M17.11 precedes 27447 + anything else).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from .models import Decision, Outcome

# Sentinel meaning "this rule does not constrain the diagnosis".
ANY = "*"


@dataclass(frozen=True)
class CoverageRule:
    """A single deterministic coverage rule."""

    rule_id: str
    description: str
    procedure_code: str  # exact CPT match, or ANY
    diagnosis_code: str  # exact ICD-10 match, or ANY
    outcome: Outcome

    def matches(self, procedure_code: str, diagnosis_code: str) -> bool:
        procedure_ok = (
            self.procedure_code == ANY or self.procedure_code == procedure_code
        )
        diagnosis_ok = (
            self.diagnosis_code == ANY or self.diagnosis_code == diagnosis_code
        )
        return procedure_ok and diagnosis_ok


# The five Phase 1 rules, in evaluation order.
COVERAGE_RULES: tuple[CoverageRule, ...] = (
    CoverageRule(
        rule_id="PAVO-R001",
        description="CPT 70553 (MRI brain, with and without contrast) is covered for any diagnosis.",
        procedure_code="70553",
        diagnosis_code=ANY,
        outcome="APPROVED",
    ),
    CoverageRule(
        rule_id="PAVO-R002",
        description=(
            "CPT 27447 (total knee arthroplasty) is covered for M17.11 "
            "(unilateral primary osteoarthritis, right knee)."
        ),
        procedure_code="27447",
        diagnosis_code="M17.11",
        outcome="APPROVED",
    ),
    CoverageRule(
        rule_id="PAVO-R003",
        description=(
            "CPT 27447 (total knee arthroplasty) with any diagnosis other than "
            "M17.11 requires human review of medical necessity."
        ),
        procedure_code="27447",
        diagnosis_code=ANY,
        outcome="ESCALATED",
    ),
    CoverageRule(
        rule_id="PAVO-R004",
        description="CPT 99214 (established patient office visit, moderate complexity) is covered for any diagnosis.",
        procedure_code="99214",
        diagnosis_code=ANY,
        outcome="APPROVED",
    ),
    CoverageRule(
        rule_id="PAVO-R005",
        description="No coverage rule is defined for this procedure code; route to a human reviewer.",
        procedure_code=ANY,
        diagnosis_code=ANY,
        outcome="ESCALATED",
    ),
)


def normalize_code(code: Optional[str]) -> str:
    """Trim and upper-case a clinical code for comparison."""
    return (code or "").strip().upper()


def find_matching_rule(
    procedure_code: str,
    diagnosis_code: str,
    rules: tuple[CoverageRule, ...] = COVERAGE_RULES,
) -> CoverageRule:
    """Return the first rule matching this procedure/diagnosis pair.

    COVERAGE_RULES ends with a catch-all, so this always resolves.
    """
    procedure = normalize_code(procedure_code)
    diagnosis = normalize_code(diagnosis_code)

    for rule in rules:
        if rule.matches(procedure, diagnosis):
            return rule

    # Defensive: only reachable if the catch-all is removed from the rule set.
    raise LookupError(
        f"No coverage rule matched procedure={procedure!r} diagnosis={diagnosis!r} "
        "and the rule set has no catch-all."
    )


def extract_procedure(fhir_bundle: dict[str, Any]) -> str:
    """Pull the CPT code out of a FHIR R4 bundle."""
    for entry in fhir_bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "ServiceRequest":
            for coding in resource.get("code", {}).get("coding", []):
                if coding.get("code"):
                    return normalize_code(coding["code"])
    return ""


def extract_diagnosis(fhir_bundle: dict[str, Any]) -> str:
    """Pull the ICD-10 code out of a FHIR R4 bundle."""
    for entry in fhir_bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Condition":
            for coding in resource.get("code", {}).get("coding", []):
                if coding.get("code"):
                    return normalize_code(coding["code"])
    return ""


def evaluate_request(
    fhir_bundle: dict[str, Any],
    coverage_rules: tuple[CoverageRule, ...] = COVERAGE_RULES,
) -> Decision:
    """Evaluate a FHIR bundle against the coverage rules.

    Phase 1 is fully deterministic: every match is definitive and carries
    confidence 1.0. The ML classifier arrives in a later phase, at which point
    non-definitive matches fall through to it and escalate below threshold.
    """
    procedure = extract_procedure(fhir_bundle)
    diagnosis = extract_diagnosis(fhir_bundle)

    rule = find_matching_rule(procedure, diagnosis, coverage_rules)

    return Decision(
        outcome=rule.outcome,
        rule_id=rule.rule_id,
        rule_description=rule.description,
        confidence=1.0,
        is_definitive=True,
    )
