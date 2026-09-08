"""Insure: document parsing, CPT mapping, pricing, and ranking."""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.db import reset_repository
from app.insure.claude import ClaudeResponseError, extract_json_object
from app.insure.facilities import base_rate_for_cpt, get_facility_pricing
from app.insure.ranking import (
    coinsurance_rate,
    estimate_member_cost,
    is_deductible_met,
    rank_facilities,
)
from app.main import app
from app.storage import reset_file_store

# A one-pixel PNG, enough to exercise the upload path.
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d494844520000000100000001080600000"
    "01f15c4890000000a49444154789c6300010000050001` 0d0a2db4000"
    "0000049454e44ae426082".replace("` ", "").replace(" ", "")
)

PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"


@pytest.fixture(autouse=True)
def clean_state():
    reset_repository()
    reset_file_store()
    yield
    reset_repository()
    reset_file_store()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def upload_documents(client: TestClient, member_id: str | None = None):
    data = {"member_id": member_id} if member_id else {}
    return client.post(
        "/api/insure/parse",
        files={
            "card_image": ("card.png", io.BytesIO(PNG_BYTES), "image/png"),
            "eoc_pdf": ("eoc.pdf", io.BytesIO(PDF_BYTES), "application/pdf"),
        },
        data=data,
    )


# ----------------------------------------------------------------- parsing


def test_parse_returns_merged_plan(client):
    response = upload_documents(client)
    assert response.status_code == 201

    body = response.json()
    plan = body["insurance_plan"]

    # Card fields.
    assert "plan_name" in plan
    assert "network_name" in plan
    # EOC fields.
    assert "deductible_individual" in plan
    assert "coinsurance_percentage" in plan
    assert isinstance(plan["covered_services"], list)


def test_parse_labels_which_parser_ran(client):
    """Without an API key the sample parser runs, and says so."""
    body = upload_documents(client).json()
    assert body["sources"] == {"card": "sample", "eoc": "sample"}


def test_parse_stores_files_and_document(client):
    body = upload_documents(client).json()

    assert body["card_image_url"].endswith(".png")
    assert body["eoc_url"].endswith(".pdf")
    assert "insure-documents" in body["card_image_url"]
    assert body["document_id"]


def test_member_id_is_hashed_everywhere(client):
    body = upload_documents(client, member_id="mbr-12345-jane-doe").json()

    assert body["member_id"].startswith("mem_")
    assert "jane" not in body["member_id"].lower()
    # The member ID read off the card is hashed too.
    assert body["insurance_plan"]["member_id"].startswith("mem_")
    # And the raw value never reaches the storage path.
    assert "jane" not in body["card_image_url"].lower()


def test_parse_rejects_non_pdf_eoc(client):
    response = client.post(
        "/api/insure/parse",
        files={
            "card_image": ("card.png", io.BytesIO(PNG_BYTES), "image/png"),
            "eoc_pdf": ("eoc.txt", io.BytesIO(b"not a pdf"), "text/plain"),
        },
    )
    assert response.status_code == 422


def test_parse_rejects_unsupported_image_type(client):
    response = client.post(
        "/api/insure/parse",
        files={
            "card_image": ("card.gif", io.BytesIO(b"GIF89a"), "image/gif"),
            "eoc_pdf": ("eoc.pdf", io.BytesIO(PDF_BYTES), "application/pdf"),
        },
    )
    assert response.status_code == 422


def test_parse_rejects_empty_upload(client):
    response = client.post(
        "/api/insure/parse",
        files={
            "card_image": ("card.png", io.BytesIO(b""), "image/png"),
            "eoc_pdf": ("eoc.pdf", io.BytesIO(PDF_BYTES), "application/pdf"),
        },
    )
    assert response.status_code == 422


# ------------------------------------------------------------------ pricing


def test_query_returns_five_ranked_facilities(client):
    document = upload_documents(client).json()

    response = client.post(
        "/api/insure/query",
        json={
            "procedure_name": "MRI of my knee",
            "document_id": document["document_id"],
        },
    )
    assert response.status_code == 201

    body = response.json()
    assert len(body["results"]) == 5
    assert body["cpt_code"]
    assert [facility["rank"] for facility in body["results"]] == [1, 2, 3, 4, 5]


def test_results_are_sorted_by_what_the_member_pays(client):
    document = upload_documents(client).json()
    body = client.post(
        "/api/insure/query",
        json={"procedure_name": "MRI knee", "document_id": document["document_id"]},
    ).json()

    paid = [facility["you_pay"] for facility in body["results"]]
    assert paid == sorted(paid)


def test_every_facility_carries_quality_and_distance(client):
    document = upload_documents(client).json()
    body = client.post(
        "/api/insure/query",
        json={"procedure_name": "colonoscopy", "document_id": document["document_id"]},
    ).json()

    for facility in body["results"]:
        assert 1 <= facility["quality_score"] <= 5
        assert facility["distance_miles"] > 0
        assert facility["payment_method"] in {"cash", "insurance"}
        assert facility["breakdown"]["formula"]


def test_query_accepts_an_inline_plan(client):
    response = client.post(
        "/api/insure/query",
        json={
            "procedure_name": "MRI brain",
            "insurance_plan": {
                "deductible_individual": 2000,
                "deductible_met": 0,
                "coinsurance_percentage": 20,
            },
        },
    )
    assert response.status_code == 201
    assert response.json()["deductible_met"] is False


def test_query_without_a_plan_is_rejected(client):
    response = client.post("/api/insure/query", json={"procedure_name": "MRI knee"})
    assert response.status_code == 422


def test_query_with_unknown_document_returns_404(client):
    response = client.post(
        "/api/insure/query",
        json={
            "procedure_name": "MRI knee",
            "document_id": "11111111-2222-3333-4444-555555555555",
        },
    )
    assert response.status_code == 404


def test_results_can_be_fetched_by_id(client):
    document = upload_documents(client).json()
    created = client.post(
        "/api/insure/query",
        json={"procedure_name": "MRI knee", "document_id": document["document_id"]},
    ).json()

    fetched = client.get(f"/api/insure/results/{created['query_id']}").json()
    assert fetched["query_id"] == created["query_id"]
    assert len(fetched["results"]) == 5


def test_every_query_writes_to_the_audit_log(client):
    document = upload_documents(client).json()
    created = client.post(
        "/api/insure/query",
        json={"procedure_name": "MRI knee", "document_id": document["document_id"]},
    ).json()

    trail = client.get(f"/api/audit/{created['query_id']}").json()
    assert len(trail) == 1
    assert trail[0]["entity_type"] == "price_query"
    assert trail[0]["action"] == "price_query.completed"
    assert trail[0]["after_state"]["cpt_code"] == created["cpt_code"]


# ------------------------------------------------------- facilities & ranking


def test_cash_prices_are_60_to_80_percent_below_negotiated():
    for cpt_code in ["70553", "73721", "27447", "45378", "99214"]:
        for facility in get_facility_pricing(cpt_code):
            discount = 1 - (facility["cash_price"] / facility["negotiated_rate"])
            assert 0.60 <= discount <= 0.80


def test_pricing_is_deterministic_per_cpt_code():
    assert get_facility_pricing("70553") == get_facility_pricing("70553")
    assert get_facility_pricing("70553") != get_facility_pricing("27447")


def test_price_bands_track_procedure_complexity():
    # Knee replacement should cost far more than an office visit.
    assert base_rate_for_cpt("27447") > base_rate_for_cpt("70553")
    assert base_rate_for_cpt("70553") > base_rate_for_cpt("99214")


def test_deductible_not_met_takes_the_cheaper_of_cash_or_coinsurance():
    amount, method, breakdown = estimate_member_cost(
        negotiated_rate=2000.0,
        cash_price=500.0,
        coinsurance=0.2,
        deductible_met=False,
    )
    # coinsurance cost is 400, cash is 500 -> insurance wins.
    assert amount == 400.0
    assert method == "insurance"
    assert breakdown["rule"] == "deductible_not_met"


def test_deductible_not_met_picks_cash_when_it_is_cheaper():
    amount, method, _ = estimate_member_cost(
        negotiated_rate=2000.0,
        cash_price=300.0,
        coinsurance=0.2,
        deductible_met=False,
    )
    assert amount == 300.0
    assert method == "cash"


def test_deductible_met_always_uses_coinsurance():
    amount, method, breakdown = estimate_member_cost(
        negotiated_rate=2000.0,
        cash_price=100.0,
        coinsurance=0.2,
        deductible_met=True,
    )
    # Cash is cheaper, but a met deductible means the insurance rate applies.
    assert amount == 400.0
    assert method == "insurance"
    assert breakdown["rule"] == "deductible_met"


def test_deductible_met_detection():
    assert is_deductible_met({"deductible_individual": 2000, "deductible_met": 2000})
    assert is_deductible_met({"deductible_individual": 2000, "deductible_met": 2500})
    assert not is_deductible_met({"deductible_individual": 2000, "deductible_met": 500})
    # Unknown values are treated as not met.
    assert not is_deductible_met({})


def test_coinsurance_parses_currency_and_percent_strings():
    assert coinsurance_rate({"coinsurance_percentage": 20}) == 0.2
    assert coinsurance_rate({"coinsurance_percentage": "20%"}) == 0.2
    assert coinsurance_rate({"coinsurance_percentage": 0.2}) == 0.2
    # Missing coinsurance falls back to the documented default.
    assert coinsurance_rate({}) == 0.2


def test_ranking_marks_which_option_is_cheaper():
    facilities = get_facility_pricing("70553")
    ranked = rank_facilities(
        facilities,
        {"deductible_individual": 2000, "deductible_met": 0, "coinsurance_percentage": 20},
    )

    for facility in ranked:
        breakdown = facility["breakdown"]
        expected = min(breakdown["cash_cost"], breakdown["insurance_cost"])
        assert facility["you_pay"] == expected


# --------------------------------------------------------------- JSON parsing


def test_extract_json_unwraps_a_fenced_block():
    assert extract_json_object('```json\n{"cpt_code": "70553"}\n```') == {
        "cpt_code": "70553"
    }


def test_extract_json_rejects_prose():
    with pytest.raises(ClaudeResponseError):
        extract_json_object("I could not read that document.")


def test_extract_json_rejects_a_bare_array():
    with pytest.raises(ClaudeResponseError):
        extract_json_object("[1, 2, 3]")


def test_health_reports_the_insure_dependencies(client):
    body = client.get("/health").json()
    assert body["file_store_backend"] == "in-memory"
    assert body["claude_configured"] is False
