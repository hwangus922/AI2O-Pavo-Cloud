"""Mock FHIR R4 bundle assembly.

Phase 1 synthesizes a bundle from the order codes rather than reading a real
EHR. The shape is what a Provider Agent would assemble from a patient chart,
so the rule engine and downstream agents work against a realistic structure.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .hashing import hash_identifier

# Human-readable labels for the codes Phase 1 knows about. Unknown codes still
# produce a valid bundle, just without a display string.
CPT_DISPLAY: dict[str, str] = {
    "70553": "MRI brain without and with contrast",
    "27447": "Arthroplasty, knee, condyle and plateau (total knee replacement)",
    "99214": "Office or other outpatient visit, established patient, moderate complexity",
}

ICD10_DISPLAY: dict[str, str] = {
    "M17.11": "Unilateral primary osteoarthritis, right knee",
    "M17.12": "Unilateral primary osteoarthritis, left knee",
    "G43.909": "Migraine, unspecified, not intractable, without status migrainosus",
    "R51.9": "Headache, unspecified",
    "Z00.00": "Encounter for general adult medical examination without abnormal findings",
}

CPT_SYSTEM = "http://www.ama-assn.org/go/cpt"
ICD10_SYSTEM = "http://hl7.org/fhir/sid/icd-10-cm"


def hash_patient_id(patient_id: Optional[str]) -> str:
    """Hash a patient identifier. Raw PHI is never stored."""
    return hash_identifier(patient_id, "pat")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_fhir_bundle(
    procedure_code: str,
    diagnosis_code: str,
    hashed_patient_id: str,
    provider_npi: Optional[str] = None,
) -> dict[str, Any]:
    """Assemble a FHIR R4 collection bundle for a prior-auth request.

    The bundle carries three resources: the hashed Patient, the Condition
    holding the diagnosis, and the ServiceRequest holding the ordered
    procedure.
    """
    procedure_code = (procedure_code or "").strip().upper()
    diagnosis_code = (diagnosis_code or "").strip().upper()
    timestamp = _now_iso()

    patient_ref = f"Patient/{hashed_patient_id}"
    condition_id = f"cond-{uuid.uuid4()}"
    service_request_id = f"sr-{uuid.uuid4()}"

    procedure_coding: dict[str, Any] = {
        "system": CPT_SYSTEM,
        "code": procedure_code,
    }
    if procedure_code in CPT_DISPLAY:
        procedure_coding["display"] = CPT_DISPLAY[procedure_code]

    diagnosis_coding: dict[str, Any] = {
        "system": ICD10_SYSTEM,
        "code": diagnosis_code,
    }
    if diagnosis_code in ICD10_DISPLAY:
        diagnosis_coding["display"] = ICD10_DISPLAY[diagnosis_code]

    requester: dict[str, Any] = {"display": "Ordering provider"}
    if provider_npi:
        requester["identifier"] = {
            "system": "http://hl7.org/fhir/sid/us-npi",
            "value": provider_npi,
        }

    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "collection",
        "timestamp": timestamp,
        "entry": [
            {
                "fullUrl": f"urn:uuid:{hashed_patient_id}",
                "resource": {
                    "resourceType": "Patient",
                    "id": hashed_patient_id,
                    "identifier": [
                        {
                            "system": "urn:pavo:patient-hash",
                            "value": hashed_patient_id,
                        }
                    ],
                },
            },
            {
                "fullUrl": f"urn:uuid:{condition_id}",
                "resource": {
                    "resourceType": "Condition",
                    "id": condition_id,
                    "subject": {"reference": patient_ref},
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active",
                            }
                        ]
                    },
                    "code": {
                        "coding": [diagnosis_coding],
                        "text": ICD10_DISPLAY.get(diagnosis_code, diagnosis_code),
                    },
                    "recordedDate": timestamp,
                },
            },
            {
                "fullUrl": f"urn:uuid:{service_request_id}",
                "resource": {
                    "resourceType": "ServiceRequest",
                    "id": service_request_id,
                    "status": "draft",
                    "intent": "order",
                    "priority": "routine",
                    "subject": {"reference": patient_ref},
                    "authoredOn": timestamp,
                    "requester": requester,
                    "reasonReference": [{"reference": f"Condition/{condition_id}"}],
                    "code": {
                        "coding": [procedure_coding],
                        "text": CPT_DISPLAY.get(procedure_code, procedure_code),
                    },
                },
            },
        ],
    }
