#!/usr/bin/env node
/*
 * Verify a groth16 proof against the circuit's verification key.
 *
 * Reads {proof, publicSignals} as JSON on stdin, writes {verified} on stdout.
 */
const fs = require("fs");
const path = require("path");
const snarkjs = require("snarkjs");

const VKEY = path.join(__dirname, "artifacts", "verification_key.json");

async function main() {
  if (!fs.existsSync(VKEY)) {
    throw new Error("Missing verification_key.json. Run zk/build.sh first.");
  }

  const { proof, publicSignals } = JSON.parse(fs.readFileSync(0, "utf-8"));
  if (!proof || !publicSignals) {
    throw new Error("Expected both proof and publicSignals.");
  }

  const verificationKey = JSON.parse(fs.readFileSync(VKEY, "utf-8"));
  const verified = await snarkjs.groth16.verify(
    verificationKey,
    publicSignals,
    proof
  );

  process.stdout.write(JSON.stringify({ verified }));
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    process.stderr.write(String(error && error.message ? error.message : error));
    process.exit(1);
  });
