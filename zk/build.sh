#!/usr/bin/env bash
# Compile the patient-criteria circuit and run a local groth16 setup.
#
# Produces everything the backend needs to prove and verify:
#   artifacts/patient_criteria.wasm  witness generator
#   artifacts/patient_criteria.zkey  proving key
#   artifacts/verification_key.json  verification key
#
# Requires the circom compiler on PATH (or at $CIRCOM). Build it once with:
#   git clone https://github.com/iden3/circom && cd circom && cargo build --release
#
# The Powers of Tau ceremony below runs locally, so no download is needed.
# That also means the toxic waste is known to whoever runs it: these
# artifacts are fine for a prototype and must never secure real value.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ART="$HERE/artifacts"
CIRCOM="${CIRCOM:-circom}"
SNARKJS="$HERE/node_modules/.bin/snarkjs"

# 2^12 constraints is ample for this circuit (it uses a few hundred).
POT_POWER=12

mkdir -p "$ART"
cd "$ART"

echo "==> Compiling the circuit"
"$CIRCOM" "$HERE/../circuits/patient_criteria.circom" \
  --r1cs --wasm --output "$ART" \
  -l "$HERE/node_modules/circomlib/circuits"

# circom nests the witness generator; lift it to a stable path.
mv -f patient_criteria_js/patient_criteria.wasm patient_criteria.wasm
rm -rf patient_criteria_js

echo "==> Powers of Tau (phase 1, local ceremony)"
"$SNARKJS" powersoftau new bn128 "$POT_POWER" pot_0000.ptau -v
"$SNARKJS" powersoftau contribute pot_0000.ptau pot_0001.ptau \
  --name="pavo-prototype" -v -e="pavo cloud prototype entropy"
"$SNARKJS" powersoftau prepare phase2 pot_0001.ptau pot_final.ptau -v

echo "==> Groth16 setup (phase 2)"
"$SNARKJS" groth16 setup patient_criteria.r1cs pot_final.ptau circuit_0000.zkey
"$SNARKJS" zkey contribute circuit_0000.zkey patient_criteria.zkey \
  --name="pavo-prototype" -v -e="pavo cloud prototype entropy"
"$SNARKJS" zkey export verificationkey patient_criteria.zkey verification_key.json

# Intermediates are large and reproducible; only the three artifacts ship.
rm -f pot_0000.ptau pot_0001.ptau pot_final.ptau circuit_0000.zkey

echo "==> Done"
ls -la patient_criteria.wasm patient_criteria.zkey verification_key.json
