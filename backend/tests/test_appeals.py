"""Appeals: denial classification, PubMed evidence, letters, and decisions."""
from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.appeals.classifier import classify_denial
from app.appeals.letter import summarize_fhir_bundle
from app.appeals.pubmed import (
    PubMedError,
    build_query,
    fetch_articles,
    find_supporting_evidence,
    format_citations,
    parse_articles,
    search_ids,
)
from app.db import reset_repository
from app.keyring import reset_keyring
from app.main import app

# An efetch response trimmed to the shapes the parser must handle: a labelled
# multi-section abstract, a collective author, and a MedlineDate-only record.
EFETCH_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID Version="1">31234567</PMID>
      <Article>
        <Journal>
          <Title>The Journal of Bone and Joint Surgery</Title>
          <JournalIssue><PubDate><Year>2019</Year></PubDate></JournalIssue>
        </Journal>
        <ArticleTitle>Outcomes of Total Knee Arthroplasty in Primary Osteoarthritis</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">Knee arthroplasty relieves pain.</AbstractText>
          <AbstractText Label="RESULTS">Function improved at 12 months.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author><LastName>Reyes</LastName><Initials>AM</Initials></Author>
          <Author><LastName>Okafor</LastName><Initials>C</Initials></Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID Version="1">28899001</PMID>
      <Article>
        <Journal>
          <Title>Osteoarthritis and Cartilage</Title>
          <JournalIssue><PubDate><MedlineDate>2017 Jul-Aug</MedlineDate></PubDate></JournalIssue>
        </Journal>
        <ArticleTitle>Conservative Management Before Arthroplasty</ArticleTitle>
        <Abstract><AbstractText>Trial of conservative therapy is recommended.</AbstractText></Abstract>
        <AuthorList>
          <Author><CollectiveName>OARSI Working Group</CollectiveName></Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""

ESEARCH_JSON = {"esearchresult": {"idlist": ["31234567", "28899001", "27000111"]}}


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


def denied_request(client: TestClient) -> dict:
    """Create a request, then force it to denied so it can be appealed."""
    from app.db import get_repository

    created = client.post(
        "/api/auth/request",
        json={"procedure_code": "27447", "diagnosis_code": "M17.12"},
    ).json()

    request_id = created["request"]["id"]
    get_repository().update_auth_request(request_id, {"status": "denied"})
    return get_repository().get_auth_request(request_id)


# ------------------------------------------------------------- classification


@pytest.mark.parametrize(
    "code,expected",
    [
        ("MN-001", "medical_necessity"),
        ("50", "medical_necessity"),
        ("NC-001", "not_covered"),
        ("96", "not_covered"),
        ("204", "not_covered"),
        ("MI-001", "missing_info"),
        ("16", "missing_info"),
        ("Not deemed medically necessary", "medical_necessity"),
        ("Service is not covered under the plan", "not_covered"),
        ("Missing clinical documentation", "missing_info"),
        ("Insufficient records submitted", "missing_info"),
        ("Procedure is considered experimental", "medical_necessity"),
        ("ZZ-999", "other"),
        ("", "other"),
        (None, "other"),
    ],
)
def test_denial_classification(code, expected):
    assert classify_denial(code) == expected


def test_classification_is_case_insensitive():
    assert classify_denial("mn-001") == "medical_necessity"
    assert classify_denial("NOT COVERED under plan") == "not_covered"


# --------------------------------------------------------------------- PubMed


def test_build_query_combines_procedure_and_diagnosis():
    query = build_query("Total knee arthroplasty", "Osteoarthritis, right knee")
    assert "Total knee arthroplasty" in query
    assert "AND" in query


def test_build_query_handles_missing_terms():
    assert build_query("", "") == ""
    assert "MRI" in build_query("MRI", "")


def test_parse_articles_extracts_every_field():
    citations = parse_articles(EFETCH_XML)
    assert len(citations) == 2

    first = citations[0]
    assert first["pmid"] == "31234567"
    assert first["title"].startswith("Outcomes of Total Knee Arthroplasty")
    assert first["authors"] == ["Reyes AM", "Okafor C"]
    assert first["journal"] == "The Journal of Bone and Joint Surgery"
    assert first["year"] == "2019"
    # Labelled sections are preserved.
    assert "BACKGROUND: Knee arthroplasty relieves pain." in first["abstract"]
    assert "RESULTS:" in first["abstract"]
    assert first["url"] == "https://pubmed.ncbi.nlm.nih.gov/31234567/"


def test_parse_articles_handles_collective_authors_and_medline_dates():
    second = parse_articles(EFETCH_XML)[1]
    assert second["authors"] == ["OARSI Working Group"]
    assert second["year"] == "2017"


def test_parse_articles_rejects_malformed_xml():
    with pytest.raises(PubMedError):
        parse_articles("<not-xml")


def test_search_and_fetch_against_a_mock_transport():
    """The esearch -> efetch handoff, exercised without network access."""

    def handler(request: httpx.Request) -> httpx.Response:
        if "esearch" in request.url.path:
            assert request.url.params["db"] == "pubmed"
            assert request.url.params["retmax"] == "3"
            return httpx.Response(200, json=ESEARCH_JSON)
        assert "efetch" in request.url.path
        # Only the ids esearch returned are fetched.
        assert request.url.params["id"] == "31234567,28899001,27000111"
        return httpx.Response(200, text=EFETCH_XML)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        pmids = search_ids("knee", client=http)
        assert pmids == ["31234567", "28899001", "27000111"]

        citations = fetch_articles(pmids, client=http)
        assert [c["pmid"] for c in citations] == ["31234567", "28899001"]


def test_find_supporting_evidence_reports_a_failure_without_raising():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="service unavailable")

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        citations, error = find_supporting_evidence("MRI knee", "Osteoarthritis", client=http)

    assert citations == []
    assert error is not None and "failed" in error.lower()


def test_fetch_with_no_ids_makes_no_request():
    assert fetch_articles([]) == []


def test_format_citations_renders_pmids():
    rendered = format_citations(parse_articles(EFETCH_XML))
    assert "PMID 31234567" in rendered
    assert "Reyes AM, Okafor C" in rendered


def test_format_citations_handles_an_empty_list():
    assert "No supporting literature" in format_citations([])


# ------------------------------------------------------------- FHIR summary


def test_fhir_summary_names_the_procedure_and_condition(client):
    created = client.post(
        "/api/auth/request",
        json={"procedure_code": "27447", "diagnosis_code": "M17.11"},
    ).json()

    summary = summarize_fhir_bundle(created["request"]["fhir_bundle"])
    assert "CPT 27447" in summary
    assert "ICD-10 M17.11" in summary
    assert "identifier hashed" in summary


def test_fhir_summary_handles_an_empty_bundle():
    assert "No FHIR bundle" in summarize_fhir_bundle({})


# ------------------------------------------------------------- appeal flow


def test_not_covered_skips_the_appeal_and_escalates(client):
    request = denied_request(client)

    body = client.post(
        f"/api/auth/{request['id']}/appeal",
        json={"denial_reason_code": "NC-001"},
    ).json()

    appeal = body["appeal"]
    assert body["denial_reason_category"] == "not_covered"
    assert appeal["status"] == "escalated"
    assert appeal["confidence"] == 0.0
    assert appeal["appeal_letter"] is None
    assert body["letter_source"] == "skipped"
    # A human gets the context they need.
    assert "not appealable on clinical grounds" in body["reviewer_notes"]


def test_low_confidence_escalates_rather_than_submitting(client):
    """The placeholder letter scores 0.0, so it must never be submitted."""
    request = denied_request(client)

    body = client.post(
        f"/api/auth/{request['id']}/appeal",
        json={"denial_reason_code": "MN-001"},
    ).json()

    appeal = body["appeal"]
    assert body["denial_reason_category"] == "medical_necessity"
    assert appeal["status"] == "escalated"
    assert appeal["confidence"] == 0.0
    assert "decision" not in body
    assert "below the 0.70 submission threshold" in body["reviewer_notes"]


def test_every_appeal_records_a_confidence_score(client):
    for code in ["MN-001", "NC-001", "MI-001", "ZZ-999"]:
        request = denied_request(client)
        appeal = client.post(
            f"/api/auth/{request['id']}/appeal",
            json={"denial_reason_code": code},
        ).json()["appeal"]

        assert appeal["confidence"] is not None
        assert 0.0 <= appeal["confidence"] <= 1.0


def test_appeal_actions_are_audited_against_the_appeal_id(client):
    request = denied_request(client)
    appeal = client.post(
        f"/api/auth/{request['id']}/appeal",
        json={"denial_reason_code": "MN-001"},
    ).json()["appeal"]

    trail = client.get(f"/api/audit/{appeal['id']}").json()
    assert [entry["action"] for entry in trail] == ["appeal.escalated"]
    assert trail[0]["entity_type"] == "appeal"

    # The request-side steps are recorded against the request.
    request_actions = [e["action"] for e in client.get(f"/api/audit/{request['id']}").json()]
    assert "appeal.denial_classified" in request_actions
    assert "appeal.evidence_retrieved" in request_actions


def test_appealing_moves_the_request_to_appealed(client):
    request = denied_request(client)
    body = client.post(
        f"/api/auth/{request['id']}/appeal",
        json={"denial_reason_code": "MN-001"},
    ).json()

    assert body["request"]["status"] == "appealed"


def test_only_a_denied_request_can_be_appealed(client):
    created = client.post(
        "/api/auth/request",
        json={"procedure_code": "70553", "diagnosis_code": "R51.9"},
    ).json()

    response = client.post(
        f"/api/auth/{created['request']['id']}/appeal",
        json={"denial_reason_code": "MN-001"},
    )
    assert response.status_code == 409


def test_appealing_an_unknown_request_returns_404(client):
    response = client.post(
        "/api/auth/11111111-2222-3333-4444-555555555555/appeal",
        json={"denial_reason_code": "MN-001"},
    )
    assert response.status_code == 404


def test_appeal_requires_a_denial_reason_code(client):
    request = denied_request(client)
    response = client.post(f"/api/auth/{request['id']}/appeal", json={})
    assert response.status_code == 422


def test_detail_page_carries_the_appeal(client):
    request = denied_request(client)
    client.post(
        f"/api/auth/{request['id']}/appeal",
        json={"denial_reason_code": "MN-001"},
    )

    detail = client.get(f"/api/auth/{request['id']}").json()
    assert len(detail["appeals"]) == 1
    assert detail["appeals"][0]["denial_reason_category"] == "medical_necessity"


# --------------------------------------------------- payer appeal decisions


def test_payer_grants_a_high_confidence_appeal(client):
    """A confident appeal is submitted over ARIA and granted."""
    from app.agents.payer import handle_appeal
    from app.aria import build_message
    from app.config import DEMO_PAYER_ORG_ID, DEMO_PROVIDER_ORG_ID
    from app.db import get_repository

    repository = get_repository()
    request = denied_request(client)

    appeal = repository.insert_appeal(
        {
            "auth_request_id": request["id"],
            "denial_reason_code": "MN-001",
            "denial_reason_category": "medical_necessity",
            "appeal_letter": "…",
            "pubmed_citations": [],
            "confidence": 0.92,
            "status": "submitted",
        }
    )

    envelope = build_message(
        payload_type="APPEAL",
        payload={
            "auth_request_id": request["id"],
            "appeal_id": appeal["id"],
            "confidence": 0.92,
        },
        sender={"agent_id": "appeals", "org_id": DEMO_PROVIDER_ORG_ID},
        receiver={"agent_id": "payer", "org_id": DEMO_PAYER_ORG_ID},
    )

    _, decision = handle_appeal(repository, envelope)

    assert decision.outcome == "APPROVED"
    assert decision.rule_id == "PAVO-A001"
    assert repository.get_appeal(appeal["id"])["status"] == "won"
    assert repository.get_auth_request(request["id"])["status"] == "approved"


def test_payer_escalates_rather_than_finally_denying(client):
    """A rejected appeal never becomes an automated final denial."""
    from app.agents.payer import handle_appeal
    from app.aria import build_message
    from app.config import DEMO_PAYER_ORG_ID, DEMO_PROVIDER_ORG_ID
    from app.db import get_repository

    repository = get_repository()
    request = denied_request(client)

    appeal = repository.insert_appeal(
        {
            "auth_request_id": request["id"],
            "denial_reason_code": "MN-001",
            "denial_reason_category": "medical_necessity",
            "appeal_letter": "…",
            "pubmed_citations": [],
            "confidence": 0.75,
            "status": "submitted",
        }
    )

    envelope = build_message(
        payload_type="APPEAL",
        payload={
            "auth_request_id": request["id"],
            "appeal_id": appeal["id"],
            "confidence": 0.75,
        },
        sender={"agent_id": "appeals", "org_id": DEMO_PROVIDER_ORG_ID},
        receiver={"agent_id": "payer", "org_id": DEMO_PAYER_ORG_ID},
    )

    _, decision = handle_appeal(repository, envelope)

    assert decision.outcome == "ESCALATED"
    assert repository.get_appeal(appeal["id"])["status"] == "lost"
    # Escalated, never denied.
    assert repository.get_auth_request(request["id"])["status"] == "escalated"


def test_an_unsigned_appeal_is_rejected(client):
    """An APPEAL with a broken signature is refused with a 401."""
    from app.aria import build_message
    from app.config import DEMO_PAYER_ORG_ID, DEMO_PROVIDER_ORG_ID

    request = denied_request(client)
    envelope = build_message(
        payload_type="APPEAL",
        payload={"auth_request_id": request["id"], "confidence": 0.95},
        sender={"agent_id": "appeals", "org_id": DEMO_PROVIDER_ORG_ID},
        receiver={"agent_id": "payer", "org_id": DEMO_PAYER_ORG_ID},
    )
    envelope["payload"]["confidence"] = 0.99

    assert client.post("/api/aria/receive", json=envelope).status_code == 401


# ------------------------------------------------------------------- stats


def test_win_rate_is_null_until_an_appeal_is_decided(client):
    stats = client.get("/api/appeals/stats").json()
    assert stats["total"] == 0
    assert stats["win_rate"] is None


def test_win_rate_counts_only_decided_appeals(client):
    from app.db import get_repository

    repository = get_repository()
    request = denied_request(client)

    for status in ["won", "won", "lost", "escalated", "submitted"]:
        repository.insert_appeal(
            {
                "auth_request_id": request["id"],
                "denial_reason_code": "MN-001",
                "denial_reason_category": "medical_necessity",
                "appeal_letter": "…",
                "pubmed_citations": [],
                "confidence": 0.8,
                "status": status,
            }
        )

    stats = client.get("/api/appeals/stats").json()
    assert stats["total"] == 5
    assert stats["decided"] == 3
    assert stats["win_rate"] == pytest.approx(2 / 3)
    assert stats["counts"]["escalated"] == 1


def test_requests_can_be_filtered_by_status(client):
    request = denied_request(client)
    client.post(
        f"/api/auth/{request['id']}/appeal",
        json={"denial_reason_code": "MN-001"},
    )
    client.post(
        "/api/auth/request",
        json={"procedure_code": "70553", "diagnosis_code": "R51.9"},
    )

    appealed = client.get("/api/auth", params={"status": "appealed"}).json()
    approved = client.get("/api/auth", params={"status": "approved"}).json()

    assert len(appealed) == 1
    assert appealed[0]["id"] == request["id"]
    assert len(approved) == 1
