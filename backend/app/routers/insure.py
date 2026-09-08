"""Insure routes: document parsing and price queries."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from .. import audit
from ..db import Repository, get_repository
from ..hashing import hash_identifier
from ..insure.claude import ClaudeResponseError, ClaudeUnavailableError
from ..insure.cpt import map_procedure_to_cpt
from ..insure.facilities import get_facility_pricing
from ..insure.parser import normalize_media_type, parse_documents
from ..insure.ranking import rank_facilities
from ..models import PriceQueryCreate
from ..storage import build_object_key, get_file_store

router = APIRouter(prefix="/api/insure", tags=["insure"])

INSURE_AGENT_ID = "agent://pavo/insure/document-parser"
PRICING_AGENT_ID = "agent://pavo/insure/pricing"

# Reject oversized uploads before they reach the parser.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _read_upload(upload: UploadFile, label: str) -> bytes:
    data = upload.file.read()
    if not data:
        raise HTTPException(status_code=422, detail=f"The {label} file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"The {label} file exceeds the 25 MB limit.",
        )
    return data


@router.post("/parse", status_code=201)
def parse_insurance_documents(
    card_image: UploadFile = File(..., description="Insurance card (JPG or PNG)"),
    eoc_pdf: UploadFile = File(..., description="Evidence of Coverage (PDF)"),
    member_id: Optional[str] = Form(default=None),
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Parse an insurance card and EOC into one insurance_plan.

    Both files are stored in the insure-documents bucket, the merged plan is
    written to insurance_documents, and the plan is returned to the caller.
    """
    card_bytes = _read_upload(card_image, "insurance card")
    eoc_bytes = _read_upload(eoc_pdf, "Evidence of Coverage")

    try:
        card_media_type = normalize_media_type(
            card_image.filename or "", card_image.content_type
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not (eoc_pdf.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            status_code=422, detail="The Evidence of Coverage must be a PDF."
        )

    hashed_member_id = hash_identifier(member_id, "mem")
    file_store = get_file_store()

    card_url = file_store.upload(
        key=build_object_key(
            member_id=hashed_member_id,
            kind="card",
            filename=card_image.filename or "card.png",
        ),
        data=card_bytes,
        content_type=card_media_type,
    )
    eoc_url = file_store.upload(
        key=build_object_key(
            member_id=hashed_member_id,
            kind="eoc",
            filename=eoc_pdf.filename or "eoc.pdf",
        ),
        data=eoc_bytes,
        content_type="application/pdf",
    )

    try:
        insurance_plan, sources = parse_documents(
            card_bytes=card_bytes,
            card_media_type=card_media_type,
            eoc_bytes=eoc_bytes,
        )
    except ClaudeUnavailableError as exc:  # pragma: no cover - guarded upstream
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ClaudeResponseError as exc:
        raise HTTPException(
            status_code=502, detail=f"Document parsing failed: {exc}"
        ) from exc

    # The member ID printed on the card is an identifier; never persist it raw.
    if insurance_plan.get("member_id"):
        insurance_plan["member_id"] = hash_identifier(
            str(insurance_plan["member_id"]), "mem"
        )

    document = repository.insert_insurance_document(
        {
            "member_id": hashed_member_id,
            "card_image_url": card_url,
            "eoc_url": eoc_url,
            "parsed_plan": insurance_plan,
        }
    )

    audit.record(
        repository,
        entity_type="insurance_document",
        entity_id=document["id"],
        action="insurance_document.parsed",
        actor_agent_id=INSURE_AGENT_ID,
        after_state={
            "card_image_url": card_url,
            "eoc_url": eoc_url,
            "parser_sources": sources,
        },
    )

    return {
        "document_id": document["id"],
        "member_id": hashed_member_id,
        "insurance_plan": insurance_plan,
        "sources": sources,
        "card_image_url": card_url,
        "eoc_url": eoc_url,
    }


@router.post("/query", status_code=201)
def create_price_query(
    payload: PriceQueryCreate,
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Price a procedure against the member's plan and rank facilities."""
    insurance_plan = payload.insurance_plan

    if not insurance_plan and payload.document_id:
        document = repository.get_insurance_document(payload.document_id)
        if document is None:
            raise HTTPException(
                status_code=404, detail="Insurance document not found."
            )
        insurance_plan = document.get("parsed_plan") or {}

    if not insurance_plan:
        raise HTTPException(
            status_code=422,
            detail="Provide insurance_plan, or a document_id to load one from.",
        )

    try:
        mapping, cpt_source = map_procedure_to_cpt(payload.procedure_name)
    except ClaudeResponseError as exc:
        raise HTTPException(
            status_code=502, detail=f"CPT mapping failed: {exc}"
        ) from exc

    cpt_code = mapping["cpt_code"]
    if not cpt_code:
        raise HTTPException(
            status_code=502, detail="Could not determine a CPT code for that procedure."
        )

    facilities = get_facility_pricing(cpt_code)
    ranked = rank_facilities(facilities, insurance_plan)

    hashed_member_id = hash_identifier(payload.member_id, "mem")

    price_query = repository.insert_price_query(
        {
            "member_id": hashed_member_id,
            "procedure_name": mapping["procedure_name"],
            "cpt_code": cpt_code,
            "insurance_plan": insurance_plan,
            "results": ranked,
        }
    )

    audit.record(
        repository,
        entity_type="price_query",
        entity_id=price_query["id"],
        action="price_query.completed",
        actor_agent_id=PRICING_AGENT_ID,
        after_state={
            "requested_procedure": payload.procedure_name,
            "cpt_code": cpt_code,
            "official_procedure_name": mapping["procedure_name"],
            "cpt_source": cpt_source,
            "facilities_returned": len(ranked),
            "best_price": ranked[0]["you_pay"] if ranked else None,
            "best_facility": ranked[0]["name"] if ranked else None,
        },
    )

    return {
        "query_id": price_query["id"],
        "cpt_code": cpt_code,
        "procedure_name": mapping["procedure_name"],
        "requested_procedure": payload.procedure_name,
        "cpt_source": cpt_source,
        "deductible_met": ranked[0]["breakdown"]["deductible_met"] if ranked else None,
        "results": ranked,
    }


@router.get("/results/{query_id}")
def get_price_query_results(
    query_id: str,
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Retrieve a stored price query and its ranked facility list."""
    price_query = repository.get_price_query(query_id)
    if price_query is None:
        raise HTTPException(status_code=404, detail="Price query not found.")

    return {
        "query_id": price_query["id"],
        "cpt_code": price_query.get("cpt_code"),
        "procedure_name": price_query.get("procedure_name"),
        "insurance_plan": price_query.get("insurance_plan"),
        "results": price_query.get("results") or [],
        "created_at": price_query.get("created_at"),
    }


@router.get("/queries")
def list_price_queries(
    limit: int = Query(default=100, ge=1, le=500),
    repository: Repository = Depends(get_repository),
) -> list[dict[str, Any]]:
    """List price queries, newest first."""
    return repository.list_price_queries(limit=limit)
