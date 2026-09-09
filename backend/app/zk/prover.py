"""Zero-knowledge proof generation and verification.

The circuit proves three coverage criteria without revealing the clinical
data behind them. Proving and verifying run through snarkjs, invoked as a
short-lived Node process against the artifacts built by zk/build.sh.

What the proof actually establishes:
  * the patient's age is at or above the payer's floor, without revealing it
  * the diagnosis hash matches the one the payer covers, without revealing
    the code
  * the deductible requirement is satisfied, without revealing any amount

What it does not: the approved-diagnosis check compares against a single
hash, so a passing proof does tell the payer the patient carries that one
diagnosis. Proving membership in a set of many codes without revealing which
needs a Merkle circuit, which is out of scope for the prototype.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Optional

# zk/ sits beside backend/ at the repository root.
ZK_ROOT = Path(__file__).resolve().parents[3] / "zk"
ARTIFACTS = ZK_ROOT / "artifacts"
PROVE_SCRIPT = ZK_ROOT / "prove.js"
VERIFY_SCRIPT = ZK_ROOT / "verify.js"

REQUIRED_ARTIFACTS = (
    ARTIFACTS / "patient_criteria.wasm",
    ARTIFACTS / "patient_criteria.zkey",
    ARTIFACTS / "verification_key.json",
)

# Proving is fast for this circuit; the ceiling is a guard against a hung
# Node process, not a realistic runtime.
TIMEOUT_SECONDS = 60

# The circuit's default policy: adults only, deductible required.
DEFAULT_MIN_AGE = 18
DEFAULT_DEDUCTIBLE_REQUIRED = 1

# Order of the circuit's public signals: three outputs, then the three
# public inputs, exactly as declared in patient_criteria.circom.
PUBLIC_SIGNAL_NAMES = (
    "age_valid",
    "diagnosis_valid",
    "deductible_valid",
    "min_age",
    "approved_diagnosis_hash",
    "deductible_required",
)


class ZkUnavailableError(RuntimeError):
    """Raised when the circuit artifacts have not been built."""


class ZkProofError(RuntimeError):
    """Raised when snarkjs fails to produce or check a proof."""


def artifacts_available() -> bool:
    """True when every circuit artifact is present."""
    return all(path.exists() for path in REQUIRED_ARTIFACTS)


def hash_diagnosis_code(diagnosis_code: str) -> int:
    """Hash an ICD-10 code into a field-safe integer.

    SHA-256 produces 256 bits, which overflows the BN254 scalar field, so the
    digest is truncated to its first 128 bits — far more than enough to keep
    distinct codes distinct, and comfortably inside the field.
    """
    digest = hashlib.sha256((diagnosis_code or "").strip().upper().encode("utf-8"))
    return int(digest.hexdigest()[:32], 16)


def _run_node(script: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Run one of the snarkjs wrapper scripts and parse its JSON output."""
    if not artifacts_available():
        missing = [p.name for p in REQUIRED_ARTIFACTS if not p.exists()]
        raise ZkUnavailableError(
            "Circuit artifacts are missing: "
            f"{', '.join(missing)}. Build them with zk/build.sh."
        )

    try:
        completed = subprocess.run(
            ["node", str(script)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=str(ZK_ROOT),
        )
    except FileNotFoundError as exc:
        raise ZkUnavailableError(
            "Node is not available; the ZK layer needs it to run snarkjs."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ZkProofError(
            f"{script.name} did not finish within {TIMEOUT_SECONDS}s."
        ) from exc

    if completed.returncode != 0:
        raise ZkProofError(
            f"{script.name} failed: {completed.stderr.strip() or 'no error output'}"
        )

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ZkProofError(
            f"{script.name} returned output that is not JSON: {completed.stdout[:200]!r}"
        ) from exc


def build_criteria(
    *,
    patient_age: int,
    diagnosis_code: str,
    deductible_met: bool,
    min_age: int = DEFAULT_MIN_AGE,
    deductible_required: int = DEFAULT_DEDUCTIBLE_REQUIRED,
) -> dict[str, Any]:
    """Assemble the circuit inputs from clinical values.

    The private half of this dict never leaves the process; only the public
    half is persisted alongside the proof.
    """
    diagnosis_hash = hash_diagnosis_code(diagnosis_code)

    # Every signal travels as a decimal string. The diagnosis hash is a
    # 128-bit integer, which JSON.parse would silently round to a float if it
    # crossed the boundary as a JSON number.
    return {
        "private": {
            "age": str(int(patient_age)),
            "diagnosis_code_hash": str(diagnosis_hash),
            "deductible_met": "1" if deductible_met else "0",
        },
        "public": {
            "min_age": str(int(min_age)),
            # The payer's approved diagnosis. In the prototype the payer
            # approves the code under review.
            "approved_diagnosis_hash": str(diagnosis_hash),
            "deductible_required": str(int(deductible_required)),
        },
    }


def generate_proof(criteria: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Produce a groth16 proof. Returns (proof, public_signals)."""
    circuit_input = {**criteria["private"], **criteria["public"]}
    result = _run_node(PROVE_SCRIPT, circuit_input)

    proof = result.get("proof")
    public_signals = result.get("publicSignals")
    if not proof or public_signals is None:
        raise ZkProofError("snarkjs did not return a proof and public signals.")

    return proof, [str(signal) for signal in public_signals]


def verify_proof(proof: dict[str, Any], public_signals: list[str]) -> bool:
    """Verify a proof against the circuit's verification key."""
    result = _run_node(
        VERIFY_SCRIPT, {"proof": proof, "publicSignals": public_signals}
    )
    return bool(result.get("verified"))


def describe_signals(public_signals: list[str]) -> dict[str, Any]:
    """Label the public signals so the UI can explain what was proven."""
    labelled = dict(zip(PUBLIC_SIGNAL_NAMES, public_signals))

    return {
        "age_valid": labelled.get("age_valid") == "1",
        "diagnosis_valid": labelled.get("diagnosis_valid") == "1",
        "deductible_valid": labelled.get("deductible_valid") == "1",
        "min_age": labelled.get("min_age"),
        "deductible_required": labelled.get("deductible_required") == "1",
    }


def proof_digest(proof: dict[str, Any]) -> str:
    """Short, stable digest of a proof, for display."""
    canonical = json.dumps(proof, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
