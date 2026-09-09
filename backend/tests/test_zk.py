"""Zero-knowledge proofs and system statistics.

These exercise the real circuit through snarkjs, so they are skipped when the
artifacts have not been built (zk/build.sh).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db import get_repository, reset_repository
from app.keyring import reset_keyring
from app.main import app
from app.routers.system import average_resolution_seconds
from app.zk.prover import (
    artifacts_available,
    build_criteria,
    describe_signals,
    hash_diagnosis_code,
    proof_digest,
)

# BN254's scalar field is just under 2^254; a truncated hash must stay below it.
BN254_FIELD_ORDER = (
    21888242871839275222246405745257275088548364400416034343698204186575808495617
)

needs_circuit = pytest.mark.skipif(
    not artifacts_available(),
    reason="Circuit artifacts are not built; run zk/build.sh.",
)


@pytest.fixture(autouse=True)
def clean_state():
    reset_keyring()
    reset_repository()
    yield
    reset_repository()
    reset_keyring()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ------------------------------------------------------------------ hashing


def test_diagnosis_hash_is_deterministic_and_normalized():
    assert hash_diagnosis_code("M17.11") == hash_diagnosis_code(" m17.11 ")
    assert hash_diagnosis_code("M17.11") != hash_diagnosis_code("M17.12")


def test_diagnosis_hash_fits_inside_the_scalar_field():
    """A full SHA-256 would overflow BN254, so the digest is truncated."""
    for code in ["M17.11", "G43.909", "Z00.00", "A" * 64]:
        assert 0 < hash_diagnosis_code(code) < BN254_FIELD_ORDER


def test_criteria_separates_private_from_public():
    criteria = build_criteria(
        patient_age=42, diagnosis_code="M17.11", deductible_met=True
    )

    assert set(criteria["private"]) == {
        "age",
        "diagnosis_code_hash",
        "deductible_met",
    }
    assert set(criteria["public"]) == {
        "min_age",
        "approved_diagnosis_hash",
        "deductible_required",
    }
    # The age must never appear on the public side.
    assert 42 not in criteria["public"].values()


def test_describe_signals_labels_the_verdicts():
    claims = describe_signals(["1", "0", "1", "18", "123", "1"])
    assert claims["age_valid"] is True
    assert claims["diagnosis_valid"] is False
    assert claims["deductible_valid"] is True
    assert claims["min_age"] == "18"


def test_proof_digest_is_stable_and_order_independent():
    assert proof_digest({"a": 1, "b": 2}) == proof_digest({"b": 2, "a": 1})
    assert proof_digest({"a": 1}) != proof_digest({"a": 2})


# ------------------------------------------------------------- real proofs


def test_status_reports_availability(client):
    body = client.get("/api/zk/status").json()
    assert body["protocol"] == "groth16"
    assert body["available"] is artifacts_available()


@needs_circuit
def test_generate_and_verify_a_real_proof(client):
    generated = client.post(
        "/api/zk/generate",
        json={"patient_age": 42, "diagnosis_code": "M17.11", "deductible_met": True},
    )
    assert generated.status_code == 201

    body = generated.json()
    assert body["proof"]["protocol"] == "groth16"
    assert body["claims"] == {
        "age_valid": True,
        "diagnosis_valid": True,
        "deductible_valid": True,
        "min_age": "18",
        "deductible_required": True,
    }

    verified = client.post(
        "/api/zk/verify",
        json={
            "proof": body["proof"],
            "public_signals": body["public_signals"],
            "proof_id": body["proof_id"],
        },
    ).json()
    assert verified["verified"] is True


@needs_circuit
def test_private_inputs_never_appear_in_the_response(client):
    """The whole point: the age is proven, not disclosed."""
    body = client.post(
        "/api/zk/generate",
        json={"patient_age": 73, "diagnosis_code": "G43.909", "deductible_met": True},
    ).json()

    assert "73" not in body["public_signals"]
    assert "patient_age" not in body
    # Nor in what was persisted.
    stored = get_repository().list_zk_proofs()[0]
    assert "73" not in str(stored["public_signals"])
    assert "age" not in stored["criteria"]


@needs_circuit
def test_a_minor_fails_the_age_criterion(client):
    body = client.post(
        "/api/zk/generate",
        json={"patient_age": 15, "diagnosis_code": "M17.11", "deductible_met": True},
    ).json()

    assert body["claims"]["age_valid"] is False
    # The proof is still valid — it honestly proves the criterion is unmet.
    verified = client.post(
        "/api/zk/verify",
        json={"proof": body["proof"], "public_signals": body["public_signals"]},
    ).json()
    assert verified["verified"] is True


@needs_circuit
def test_tampered_public_signals_fail_verification(client):
    body = client.post(
        "/api/zk/generate",
        json={"patient_age": 15, "diagnosis_code": "M17.11", "deductible_met": False},
    ).json()

    # Claim the age check passed without re-proving it.
    forged = list(body["public_signals"])
    forged[0] = "1"

    verified = client.post(
        "/api/zk/verify",
        json={"proof": body["proof"], "public_signals": forged},
    ).json()
    assert verified["verified"] is False


@needs_circuit
def test_proof_generation_is_audited(client):
    body = client.post(
        "/api/zk/generate",
        json={"patient_age": 42, "diagnosis_code": "M17.11", "deductible_met": True},
    ).json()

    trail = client.get(f"/api/audit/{body['proof_id']}").json()
    assert trail[0]["entity_type"] == "zk_proof"
    assert trail[0]["action"] == "zk_proof.generated"

    client.post(
        "/api/zk/verify",
        json={
            "proof": body["proof"],
            "public_signals": body["public_signals"],
            "proof_id": body["proof_id"],
        },
    )

    actions = [e["action"] for e in client.get(f"/api/audit/{body['proof_id']}").json()]
    assert actions == ["zk_proof.generated", "zk_proof.verified"]


@needs_circuit
def test_verification_result_is_persisted(client):
    body = client.post(
        "/api/zk/generate",
        json={"patient_age": 42, "diagnosis_code": "M17.11", "deductible_met": True},
    ).json()

    assert get_repository().get_zk_proof(body["proof_id"])["verified"] is None

    client.post(
        "/api/zk/verify",
        json={
            "proof": body["proof"],
            "public_signals": body["public_signals"],
            "proof_id": body["proof_id"],
        },
    )
    assert get_repository().get_zk_proof(body["proof_id"])["verified"] is True


@needs_circuit
def test_proof_can_be_attached_to_an_auth_request(client):
    created = client.post(
        "/api/auth/request",
        json={"procedure_code": "70553", "diagnosis_code": "G43.909"},
    ).json()

    body = client.post(
        "/api/zk/generate",
        json={
            "auth_request_id": created["request"]["id"],
            "patient_age": 42,
            "diagnosis_code": "G43.909",
            "deductible_met": True,
        },
    ).json()

    stored = get_repository().get_zk_proof(body["proof_id"])
    assert stored["auth_request_id"] == created["request"]["id"]


def test_generate_rejects_an_unknown_auth_request(client):
    response = client.post(
        "/api/zk/generate",
        json={
            "auth_request_id": "11111111-2222-3333-4444-555555555555",
            "patient_age": 42,
            "diagnosis_code": "M17.11",
            "deductible_met": True,
        },
    )
    assert response.status_code == 404


def test_generate_validates_the_age_range(client):
    response = client.post(
        "/api/zk/generate",
        json={"patient_age": 999, "diagnosis_code": "M17.11", "deductible_met": True},
    )
    assert response.status_code == 422


# ------------------------------------------------------------ system stats


def test_average_resolution_handles_missing_and_invalid_timestamps():
    assert average_resolution_seconds([]) is None
    assert average_resolution_seconds([{"created_at": "2026-01-01T00:00:00Z"}]) is None

    average = average_resolution_seconds(
        [
            {
                "created_at": "2026-01-01T00:00:00Z",
                "resolved_at": "2026-01-01T00:00:10Z",
            },
            {
                "created_at": "2026-01-01T00:00:00Z",
                "resolved_at": "2026-01-01T00:00:20Z",
            },
            # Unresolved rows are excluded rather than counted as zero.
            {"created_at": "2026-01-01T00:00:00Z", "resolved_at": None},
        ]
    )
    assert average == 15.0


def test_system_stats_counts_every_entity(client):
    client.post(
        "/api/auth/request",
        json={"procedure_code": "70553", "diagnosis_code": "G43.909"},
    )

    stats = client.get("/api/system/stats").json()
    assert stats["authorizations_processed"] == 1
    assert stats["requests_by_status"]["approved"] == 1
    assert stats["aria_messages_exchanged"] == 2
    assert stats["appeals_win_rate"] is None
    assert stats["average_resolution_seconds"] is not None


def test_activity_feed_returns_newest_first(client):
    for diagnosis in ["G43.909", "R51.9"]:
        client.post(
            "/api/auth/request",
            json={"procedure_code": "70553", "diagnosis_code": diagnosis},
        )

    feed = client.get("/api/system/activity", params={"limit": 3}).json()
    assert len(feed) == 3
    timestamps = [row["created_at"] for row in feed]
    assert timestamps == sorted(timestamps, reverse=True)


def test_audit_trail_filters_by_entity_type(client):
    client.post(
        "/api/auth/request",
        json={"procedure_code": "70553", "diagnosis_code": "G43.909"},
    )

    everything = client.get("/api/system/audit").json()
    filtered = client.get(
        "/api/system/audit", params={"entity_type": "auth_request"}
    ).json()

    assert len(everything) >= 5
    assert len(filtered) == len(everything)
    assert {row["entity_type"] for row in filtered} == {"auth_request"}

    assert client.get(
        "/api/system/audit", params={"entity_type": "price_query"}
    ).json() == []


def test_audit_trail_filters_by_date_range(client):
    client.post(
        "/api/auth/request",
        json={"procedure_code": "70553", "diagnosis_code": "G43.909"},
    )

    assert client.get("/api/system/audit", params={"since": "2020-01-01"}).json()
    assert client.get("/api/system/audit", params={"until": "2020-01-01"}).json() == []


def test_cors_allows_both_localhost_forms():
    """A browser treats localhost and 127.0.0.1 as different origins."""
    from app.config import Settings

    settings = Settings()
    assert "http://localhost:3000" in settings.cors_origins
    assert "http://127.0.0.1:3000" in settings.cors_origins


def test_cors_accepts_a_comma_separated_list(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv(
        "FRONTEND_ORIGIN", "https://demo.pavo.test, http://127.0.0.1:3010"
    )
    origins = Settings().cors_origins

    assert "https://demo.pavo.test" in origins
    assert "http://127.0.0.1:3010" in origins
    # Defaults are still present, and nothing is duplicated.
    assert "http://localhost:3000" in origins
    assert len(origins) == len(set(origins))
