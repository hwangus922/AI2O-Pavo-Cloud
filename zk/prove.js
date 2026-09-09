#!/usr/bin/env node
/*
 * Generate a groth16 proof for the patient-criteria circuit.
 *
 * Reads the circuit inputs as JSON on stdin, writes {proof, publicSignals}
 * as JSON on stdout. The private inputs are consumed here and never appear
 * in the output.
 */
const fs = require("fs");
const path = require("path");
const snarkjs = require("snarkjs");

const ARTIFACTS = path.join(__dirname, "artifacts");
const WASM = path.join(ARTIFACTS, "patient_criteria.wasm");
const ZKEY = path.join(ARTIFACTS, "patient_criteria.zkey");

const REQUIRED_INPUTS = [
  "age",
  "diagnosis_code_hash",
  "deductible_met",
  "min_age",
  "approved_diagnosis_hash",
  "deductible_required",
];

function readStdin() {
  return fs.readFileSync(0, "utf-8");
}

async function main() {
  for (const artifact of [WASM, ZKEY]) {
    if (!fs.existsSync(artifact)) {
      throw new Error(
        `Missing circuit artifact ${path.basename(artifact)}. Run zk/build.sh first.`
      );
    }
  }

  const input = JSON.parse(readStdin());

  const missing = REQUIRED_INPUTS.filter((name) => input[name] === undefined);
  if (missing.length > 0) {
    throw new Error(`Missing circuit input(s): ${missing.join(", ")}`);
  }

  // snarkjs wants every signal as a decimal string. A field element can
  // exceed Number.MAX_SAFE_INTEGER, so a signal that arrives as a JSON number
  // has already lost precision — reject it rather than prove the wrong thing.
  const witness = {};
  for (const name of REQUIRED_INPUTS) {
    const value = input[name];
    if (typeof value === "number" && !Number.isSafeInteger(value)) {
      throw new Error(
        `Input ${name} arrived as an unsafe JSON number; send it as a string.`
      );
    }
    witness[name] = String(value);
  }

  const { proof, publicSignals } = await snarkjs.groth16.fullProve(
    witness,
    WASM,
    ZKEY
  );

  process.stdout.write(JSON.stringify({ proof, publicSignals }));
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    process.stderr.write(String(error && error.message ? error.message : error));
    process.exit(1);
  });
