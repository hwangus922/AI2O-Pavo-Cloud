"""Pavo Cloud backend — FastAPI application entrypoint.

Run locally:
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import get_repository
from .storage import get_file_store
from .routers import aria, audit, auth, insure
from .rules import COVERAGE_RULES

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Builds the repository and seeds the demo organizations.
    get_repository()
    yield


app = FastAPI(
    title="Pavo Cloud API",
    version="0.1.0",
    description=(
        "Phase 1 — autonomous prior authorization over the ARIA protocol. "
        "Every decision carries the rule_id that produced it."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(aria.router)
app.include_router(audit.router)
app.include_router(insure.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, Any]:
    """Liveness probe. Reports which storage backend is active."""
    repository = get_repository()
    return {
        "status": "ok",
        "aria_version": settings.aria_version,
        "storage_backend": repository.backend_name,
        "file_store_backend": get_file_store().backend_name,
        "claude_configured": bool(settings.anthropic_api_key),
    }


@app.get("/api/rules", tags=["meta"])
def list_rules() -> list[dict[str, Any]]:
    """The active coverage rules, so the dashboard can explain any decision."""
    return [
        {
            "rule_id": rule.rule_id,
            "description": rule.description,
            "procedure_code": rule.procedure_code,
            "diagnosis_code": rule.diagnosis_code,
            "outcome": rule.outcome,
        }
        for rule in COVERAGE_RULES
    ]
