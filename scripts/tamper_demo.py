"""Stage demonstration: editing a signed request after signing gets it refused.

Runs the real application in-process against the in-memory repository, so it
needs no server and no database. It creates an authorization request, signs a
genuine ARIA envelope for it, changes one field of the payload after signing,
and posts it to the payer. The payer refuses it before reading it, and writes
the refusal to the audit trail.

    python scripts/tamper_demo.py

Output is deliberately short and readable from the back of a room.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.aria import build_message  # noqa: E402
from app.config import DEMO_PAYER_ORG_ID, DEMO_PROVIDER_ORG_ID  # noqa: E402
from app.main import app  # noqa: E402

RULE = "-" * 62


def main() -> int:
    with TestClient(app) as client:
        created = client.post(
            "/api/auth/request",
            json={"procedure_code": "27447", "diagnosis_code": "M17.11"},
        ).json()["request"]
        request_id = created["id"]

        envelope = build_message(
            payload_type="AUTH_REQUEST",
            payload={
                "auth_request_id": request_id,
                "fhir_bundle": created["fhir_bundle"],
            },
            sender={"agent_id": "a", "org_id": DEMO_PROVIDER_ORG_ID},
            receiver={"agent_id": "b", "org_id": DEMO_PAYER_ORG_ID},
        )

        print(RULE)
        print("A genuine, signed request from the provider's agent")
        print(RULE)
        print(f"  procedure code   {created['procedure_code']}")
        print(f"  signature        {envelope['signature'][:52]}...")
        honest = client.post("/api/aria/verify", json={"message": envelope})
        print(f"  verify           {honest.json()['verified']}")

        # Change one field. The signature is left exactly as it was.
        entries = envelope["payload"]["fhir_bundle"]["entry"]
        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "ServiceRequest":
                resource["code"]["coding"][0]["code"] = "70553"

        print()
        print(RULE)
        print("The same envelope, with the procedure changed after signing")
        print(RULE)
        print("  procedure code   70553   <- edited in transit")
        print(f"  signature        {envelope['signature'][:52]}...  (unchanged)")

        tampered = client.post("/api/aria/verify", json={"message": envelope})
        print(f"  verify           {tampered.json()['verified']}")

        received = client.post("/api/aria/receive", json=envelope)
        print(f"  payer replies    HTTP {received.status_code}")

        actions = [e["action"] for e in client.get(f"/api/audit/{request_id}").json()]
        print(f"  audit trail      {', '.join(actions)}")
        print()
        print("The payer refused it before reading it, and logged the refusal.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
