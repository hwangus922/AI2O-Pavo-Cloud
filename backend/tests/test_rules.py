"""Rule engine coverage — the five Phase 1 rules and code normalization."""
from __future__ import annotations

import pytest

from app.fhir import build_fhir_bundle, hash_patient_id
from app.rules import evaluate_request, find_matching_rule


def bundle(procedure_code: str, diagnosis_code: str) -> dict:
    return build_fhir_bundle(
        procedure_code=procedure_code,
        diagnosis_code=diagnosis_code,
        hashed_patient_id=hash_patient_id("patient-under-test"),
    )


@pytest.mark.parametrize(
    "procedure,diagnosis,expected_outcome,expected_rule",
    [
        # R001 — MRI brain is approved regardless of diagnosis.
        ("70553", "G43.909", "APPROVED", "PAVO-R001"),
        ("70553", "R51.9", "APPROVED", "PAVO-R001"),
        ("70553", "Z00.00", "APPROVED", "PAVO-R001"),
        # R002 — knee replacement with the matching diagnosis is approved.
        ("27447", "M17.11", "APPROVED", "PAVO-R002"),
        # R003 — knee replacement with any other diagnosis escalates.
        ("27447", "M17.12", "ESCALATED", "PAVO-R003"),
        ("27447", "Z00.00", "ESCALATED", "PAVO-R003"),
        # R004 — office visit is approved regardless of diagnosis.
        ("99214", "Z00.00", "APPROVED", "PAVO-R004"),
        ("99214", "M17.11", "APPROVED", "PAVO-R004"),
        # R005 — anything else escalates.
        ("12345", "M17.11", "ESCALATED", "PAVO-R005"),
        ("99999", "Z00.00", "ESCALATED", "PAVO-R005"),
    ],
)
def test_five_hardcoded_rules(procedure, diagnosis, expected_outcome, expected_rule):
    decision = evaluate_request(bundle(procedure, diagnosis))

    assert decision.outcome == expected_outcome
    assert decision.rule_id == expected_rule
    assert decision.confidence == 1.0
    assert decision.is_definitive is True


def test_specific_knee_rule_wins_over_catch_all():
    """R002 must be evaluated before R003, or every knee case would escalate."""
    approved = evaluate_request(bundle("27447", "M17.11"))
    escalated = evaluate_request(bundle("27447", "M17.12"))

    assert approved.rule_id == "PAVO-R002"
    assert escalated.rule_id == "PAVO-R003"


def test_codes_are_normalized_before_matching():
    """Lowercase and padded codes still hit the right rule."""
    decision = evaluate_request(bundle("  27447 ", " m17.11 "))

    assert decision.rule_id == "PAVO-R002"
    assert decision.outcome == "APPROVED"


def test_every_decision_carries_a_rule_id():
    """No black box outputs: a rule_id is always present."""
    for procedure, diagnosis in [
        ("70553", "G43.909"),
        ("27447", "M17.11"),
        ("27447", "M99.99"),
        ("99214", "Z00.00"),
        ("00000", "X00.0"),
    ]:
        decision = evaluate_request(bundle(procedure, diagnosis))
        assert decision.rule_id
        assert decision.rule_description


def test_unknown_procedure_falls_through_to_catch_all():
    rule = find_matching_rule("55555", "A00.0")
    assert rule.rule_id == "PAVO-R005"
    assert rule.outcome == "ESCALATED"


def test_status_maps_onto_persisted_values():
    assert evaluate_request(bundle("70553", "R51.9")).status == "approved"
    assert evaluate_request(bundle("27447", "M17.12")).status == "escalated"
