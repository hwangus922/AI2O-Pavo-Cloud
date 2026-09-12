#!/usr/bin/env python3
"""Seed a demo dataset for the AI2O presentation.

Run against a running backend:

    python scripts/seed_demo.py --api http://localhost:8000

Everything is created through the public API, so the data is real: the
requests run through the rule engine, the appeals through the appeals agent,
and the proofs through the actual circuit. Nothing here is fabricated.

The default backend keeps data in memory, so the seed lives as long as the
server process does. Point the backend at Supabase for a persistent demo.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

DEFAULT_API = "http://localhost:8000"

# The same sample card and Evidence of Coverage the /demo page uploads. They
# are real documents, so the seed works when Claude is doing the parsing.
SAMPLE_DOCS = Path(__file__).resolve().parents[1] / "frontend" / "public" / "demo"

# Ten requests spanning every branch of the rule engine.
AUTH_REQUESTS: tuple[tuple[str, str, str], ...] = (
    ("70553", "G43.909", "MRI brain for migraine"),
    ("70553", "R51.9", "MRI brain for headache"),
    ("70553", "Z00.00", "MRI brain, routine encounter"),
    ("27447", "M17.11", "Knee replacement, right-knee osteoarthritis"),
    ("27447", "M17.12", "Knee replacement, left-knee osteoarthritis"),
    ("27447", "Z00.00", "Knee replacement, unspecified diagnosis"),
    ("99214", "Z00.00", "Office visit, routine"),
    ("99214", "M17.11", "Office visit, osteoarthritis follow-up"),
    ("12345", "M17.11", "Unrecognized procedure code"),
    ("45378", "R51.9", "Colonoscopy, no matching rule"),
)

# Denial codes for the three seeded appeals: one submitted, two escalated.
APPEAL_CASES: tuple[tuple[str, str], ...] = (
    ("MN-001", "Medical necessity"),
    ("MI-001", "Missing documentation"),
    ("NC-001", "Not covered"),
)

PRICE_QUERIES: tuple[str, ...] = (
    "MRI of my knee",
    "MRI brain",
    "Colonoscopy",
    "Screening mammogram",
    "Office visit",
)

ZK_CASES: tuple[tuple[int, str, bool], ...] = (
    (42, "M17.11", True),
    (67, "G43.909", True),
    (29, "R51.9", False),
    (15, "M17.11", True),   # a minor: age criterion fails, honestly
    (55, "Z00.00", False),
)


class ApiError(RuntimeError):
    pass


def call(
    api: str, method: str, path: str, body: Optional[dict[str, Any]] = None
) -> Any:
    """One JSON request against the backend."""
    request = urllib.request.Request(
        f"{api}{path}",
        method=method,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:300]
        raise ApiError(f"{method} {path} -> HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise ApiError(
            f"Could not reach {api}. Is the backend running? ({error.reason})"
        ) from error


def short(identifier: Optional[str]) -> str:
    """First eight characters, matching how the UI displays an id."""
    return (identifier or "")[:8] or "—"


def table(title: str, headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    """Print a plain aligned table."""
    print(f"\n{title}")
    if not rows:
        print("  (none)")
        return

    widths = [
        max(len(str(headers[i])), max(len(str(row[i])) for row in rows))
        for i in range(len(headers))
    ]
    line = "  " + "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(line)
    print("  " + "  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        print("  " + "  ".join(str(row[i]).ljust(widths[i]) for i in range(len(row))))


def seed_organizations(api: str) -> list[tuple[str, ...]]:
    """Report the demo organizations and their signing keys.

    The backend provisions a provider and a payer with real RSA-2048 key
    pairs at startup, so this reads them back rather than creating duplicates.
    """
    health = call(api, "GET", "/health")
    rows = [
        ("storage", health["storage_backend"]),
        ("file store", health["file_store_backend"]),
        ("ARIA version", health["aria_version"]),
        ("Claude configured", str(health["claude_configured"])),
        ("ZK artifacts", str(health.get("zk_artifacts_available"))),
    ]
    return rows


def seed_auth_requests(api: str) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    for procedure, diagnosis, label in AUTH_REQUESTS:
        result = call(
            api,
            "POST",
            "/api/auth/request",
            {"procedure_code": procedure, "diagnosis_code": diagnosis},
        )
        request = result["request"]
        rows.append(
            (
                short(request["id"]),
                procedure,
                diagnosis,
                request["status"],
                request["decision_rule_id"] or "—",
                label,
            )
        )
    return rows


def seed_appeals(api: str) -> list[tuple[str, ...]]:
    """Appeal the escalated requests, one per denial category."""
    escalated = call(api, "GET", "/api/auth?status=escalated")
    rows: list[tuple[str, ...]] = []

    for (code, label), request in zip(APPEAL_CASES, escalated):
        result = call(
            api,
            "POST",
            f"/api/auth/{request['id']}/appeal",
            {"denial_reason_code": code},
        )
        appeal = result["appeal"]
        rows.append(
            (
                short(appeal["id"]),
                short(appeal["auth_request_id"]),
                code,
                appeal["denial_reason_category"],
                appeal["status"],
                f"{(appeal['confidence'] or 0):.2f}",
                str(len(result["citations"])),
                label,
            )
        )
    return rows


def seed_price_queries(api: str) -> list[tuple[str, ...]]:
    """Parse a document once, then price five procedures against that plan."""
    boundary = "----pavoseed"
    png = (SAMPLE_DOCS / "sample-card.png").read_bytes()
    pdf = (SAMPLE_DOCS / "sample-eoc.pdf").read_bytes()

    parts: list[bytes] = []
    for name, filename, content_type, payload in (
        ("card_image", "card.png", "image/png", png),
        ("eoc_pdf", "eoc.pdf", "application/pdf", pdf),
    ):
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
            + payload
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))

    upload = urllib.request.Request(
        f"{api}/api/insure/parse",
        method="POST",
        data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(upload, timeout=120) as response:
        document = json.loads(response.read().decode("utf-8"))

    rows: list[tuple[str, ...]] = []
    for procedure in PRICE_QUERIES:
        result = call(
            api,
            "POST",
            "/api/insure/query",
            {"procedure_name": procedure, "document_id": document["document_id"]},
        )
        best = result["results"][0]
        rows.append(
            (
                short(result["query_id"]),
                procedure,
                result["cpt_code"],
                f"${best['you_pay']:,.2f}",
                best["cheaper_option"],
                best["name"],
            )
        )
    return rows


def seed_zk_proofs(api: str) -> list[tuple[str, ...]]:
    status = call(api, "GET", "/api/zk/status")
    if not status["available"]:
        print(
            "\n! Skipping ZK proofs: circuit artifacts are missing. "
            "Build them with zk/build.sh."
        )
        return []

    approved = call(api, "GET", "/api/auth?status=approved")
    rows: list[tuple[str, ...]] = []

    for index, (age, diagnosis, deductible_met) in enumerate(ZK_CASES):
        request_id = approved[index]["id"] if index < len(approved) else None
        result = call(
            api,
            "POST",
            "/api/zk/generate",
            {
                "auth_request_id": request_id,
                "patient_age": age,
                "diagnosis_code": diagnosis,
                "deductible_met": deductible_met,
            },
        )
        verified = call(
            api,
            "POST",
            "/api/zk/verify",
            {
                "proof": result["proof"],
                "public_signals": result["public_signals"],
                "proof_id": result["proof_id"],
            },
        )
        claims = result["claims"]
        rows.append(
            (
                short(result["proof_id"]),
                short(request_id),
                "yes" if claims["age_valid"] else "no",
                "yes" if claims["diagnosis_valid"] else "no",
                "yes" if claims["deductible_valid"] else "no",
                str(verified["verified"]),
                result["proof_digest"][7:19],
            )
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api", default=DEFAULT_API, help=f"Backend origin (default {DEFAULT_API})"
    )
    args = parser.parse_args()
    api = args.api.rstrip("/")

    try:
        print(f"Seeding demo data against {api}")

        table("Environment", ("setting", "value"), seed_organizations(api))

        table(
            "Authorization requests",
            ("id", "cpt", "icd-10", "status", "rule", "note"),
            seed_auth_requests(api),
        )
        table(
            "Appeals",
            ("id", "request", "code", "category", "status", "conf", "cites", "note"),
            seed_appeals(api),
        )
        table(
            "Price queries",
            ("id", "procedure", "cpt", "you pay", "cheaper", "facility"),
            seed_price_queries(api),
        )
        table(
            "ZK proofs",
            ("id", "request", "age", "dx", "deduct", "verified", "digest"),
            seed_zk_proofs(api),
        )

        stats = call(api, "GET", "/api/system/stats")
        table(
            "System totals",
            ("metric", "value"),
            [
                ("Authorizations processed", str(stats["authorizations_processed"])),
                ("ARIA messages exchanged", str(stats["aria_messages_exchanged"])),
                ("Appeals", str(stats["appeals_total"])),
                ("ZK proofs generated", str(stats["zk_proofs_generated"])),
                ("Price queries", str(stats["price_queries"])),
            ],
        )

        print("\nDone. Open /demo for the walkthrough, /audit for the full trail.")
        return 0

    except ApiError as error:
        print(f"\nSeeding failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
