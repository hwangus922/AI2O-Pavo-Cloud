"""End-to-end flow: webhook -> provider agent -> payer agent -> audit trail."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.aria import build_message, verify_message
from app.db import reset_repository
from app.main import app


@pytest.fixture(autouse=True)
def clean_repository():
    """Give every test a fresh in-memory store."""
    reset_repository()
    yield
    reset_repository()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_reports_storage_backend(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["storage_backend"] == "in-memory"


def test_webhook_approves_mri_brain(client):
    response = client.post(
        "/api/auth/request",
        json={"procedure_code": "70553", "diagnosis_code": "G43.909"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["decision"]["outcome"] == "APPROVED"
    assert body["decision"]["rule_id"] == "PAVO-R001"
    assert body["request"]["status"] == "approved"
    assert body["request"]["decision_rule_id"] == "PAVO-R001"
    assert body["request"]["resolved_at"] is not None


def test_webhook_escalates_unmatched_knee_diagnosis(client):
    response = client.post(
        "/api/auth/request",
        json={"procedure_code": "27447", "diagnosis_code": "M17.12"},
    )

    body = response.json()
    assert body["decision"]["outcome"] == "ESCALATED"
    assert body["request"]["status"] == "escalated"
    assert body["request"]["decision_rule_id"] == "PAVO-R003"


def test_raw_patient_id_is_never_stored(client):
    response = client.post(
        "/api/auth/request",
        json={
            "procedure_code": "99214",
            "diagnosis_code": "Z00.00",
            "patient_id": "mrn-12345-jane-doe",
        },
    )

    stored = response.json()["request"]["patient_id"]
    assert stored != "mrn-12345-jane-doe"
    assert "jane" not in stored.lower()
    assert stored.startswith("pat_")


def test_fhir_bundle_is_assembled_from_the_order(client):
    response = client.post(
        "/api/auth/request",
        json={"procedure_code": "70553", "diagnosis_code": "R51.9"},
    )

    bundle = response.json()["request"]["fhir_bundle"]
    assert bundle["resourceType"] == "Bundle"

    resource_types = {e["resource"]["resourceType"] for e in bundle["entry"]}
    assert resource_types == {"Patient", "Condition", "ServiceRequest"}


def test_detail_returns_full_aria_thread_and_audit_trail(client):
    created = client.post(
        "/api/auth/request",
        json={"procedure_code": "27447", "diagnosis_code": "M17.11"},
    ).json()
    request_id = created["request"]["id"]

    detail = client.get(f"/api/auth/{request_id}").json()

    payload_types = [m["payload_type"] for m in detail["aria_messages"]]
    assert payload_types == ["AUTH_REQUEST", "AUTH_RESPONSE"]
    assert all(m["verified"] for m in detail["aria_messages"])

    actions = [entry["action"] for entry in detail["audit_log"]]
    assert "auth_request.created" in actions
    assert "aria.auth_request.sent" in actions
    assert "aria.auth_request.received" in actions
    assert "decision.rendered" in actions
    assert "aria.auth_response.sent" in actions


def test_every_decision_writes_its_rule_id_to_the_audit_log(client):
    created = client.post(
        "/api/auth/request",
        json={"procedure_code": "27447", "diagnosis_code": "M99.99"},
    ).json()
    request_id = created["request"]["id"]

    trail = client.get(f"/api/audit/{request_id}").json()
    decisions = [e for e in trail if e["action"] == "decision.rendered"]

    assert len(decisions) == 1
    assert decisions[0]["after_state"]["decision_rule_id"] == "PAVO-R003"
    assert decisions[0]["after_state"]["rule_description"]
    assert decisions[0]["before_state"]["status"] == "pending"


def test_list_returns_newest_first(client):
    for diagnosis in ["G43.909", "R51.9", "Z00.00"]:
        client.post(
            "/api/auth/request",
            json={"procedure_code": "70553", "diagnosis_code": diagnosis},
        )

    listed = client.get("/api/auth").json()
    assert len(listed) == 3

    created_ats = [row["created_at"] for row in listed]
    assert created_ats == sorted(created_ats, reverse=True)


def test_missing_request_returns_404(client):
    response = client.get("/api/auth/11111111-2222-3333-4444-555555555555")
    assert response.status_code == 404


def test_validation_rejects_empty_codes(client):
    response = client.post(
        "/api/auth/request",
        json={"procedure_code": "", "diagnosis_code": "M17.11"},
    )
    assert response.status_code == 422


def test_aria_signature_round_trip():
    envelope = build_message(
        payload_type="AUTH_REQUEST",
        payload={"procedure_code": "70553"},
        sender={"agent_id": "a", "org_id": "o"},
        receiver={"agent_id": "b", "org_id": "p"},
    )

    verified, reason = verify_message(envelope)
    assert verified is True
    assert reason is None


def test_tampered_envelope_fails_verification(client):
    envelope = build_message(
        payload_type="AUTH_REQUEST",
        payload={"procedure_code": "70553"},
        sender={"agent_id": "a", "org_id": "o"},
        receiver={"agent_id": "b", "org_id": "p"},
    )
    envelope["payload"]["procedure_code"] = "27447"

    response = client.post("/api/aria/verify", json={"message": envelope})
    assert response.json()["verified"] is False

    receive = client.post("/api/aria/receive", json=envelope)
    assert receive.status_code == 401


def test_aria_receive_handles_a_signed_auth_request(client):
    created = client.post(
        "/api/auth/request",
        json={"procedure_code": "70553", "diagnosis_code": "R51.9"},
    ).json()

    envelope = build_message(
        payload_type="AUTH_REQUEST",
        payload={
            "auth_request_id": created["request"]["id"],
            "fhir_bundle": created["request"]["fhir_bundle"],
        },
        sender={"agent_id": "a", "org_id": "o"},
        receiver={"agent_id": "b", "org_id": "p"},
    )

    response = client.post("/api/aria/receive", json=envelope)
    assert response.status_code == 200
    assert response.json()["decision"]["rule_id"] == "PAVO-R001"


def test_rules_endpoint_lists_all_five_rules(client):
    rules = client.get("/api/rules").json()
    assert [r["rule_id"] for r in rules] == [
        "PAVO-R001",
        "PAVO-R002",
        "PAVO-R003",
        "PAVO-R004",
        "PAVO-R005",
    ]
