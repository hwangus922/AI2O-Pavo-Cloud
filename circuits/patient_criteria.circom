pragma circom 2.0.0;

include "comparators.circom";

/*
 * PatientCriteria — proves three coverage criteria without revealing the
 * clinical data behind them.
 *
 * Private inputs (never leave the provider):
 *   age                  the patient's age in years
 *   diagnosis_code_hash  truncated SHA-256 of the ICD-10 code
 *   deductible_met       1 if the deductible is met, 0 otherwise
 *
 * Public inputs (shared with the payer):
 *   min_age                  the age floor the payer requires
 *   approved_diagnosis_hash  hash of the diagnosis the payer covers
 *   deductible_required      1 if the payer requires a met deductible
 *
 * Outputs are public by construction and carry the three verdicts.
 *
 * Note on circom 2: the `private` keyword was removed. A signal is private
 * unless it is named in the `public` list on `component main`, so the three
 * clinical inputs below stay private without any keyword.
 */
template PatientCriteria() {
    signal input age;
    signal input diagnosis_code_hash;
    signal input deductible_met;

    signal input min_age;
    signal input approved_diagnosis_hash;
    signal input deductible_required;

    signal output age_valid;
    signal output diagnosis_valid;
    signal output deductible_valid;

    // age >= min_age. 8 bits covers any human age.
    component age_check = GreaterEqThan(8);
    age_check.in[0] <== age;
    age_check.in[1] <== min_age;
    age_valid <== age_check.out;

    // The diagnosis hash matches the one the payer approves. circom has no
    // ternary operator, so equality comes from IsEqual, which outputs 1 or 0.
    component diagnosis_check = IsEqual();
    diagnosis_check.in[0] <== diagnosis_code_hash;
    diagnosis_check.in[1] <== approved_diagnosis_hash;
    diagnosis_valid <== diagnosis_check.out;

    // Satisfied when the deductible is not required, or when it is met.
    component not_required = IsZero();
    not_required.in <== deductible_required;

    component is_met = IsEqual();
    is_met.in[0] <== deductible_met;
    is_met.in[1] <== 1;

    // Boolean OR, written arithmetically: a + b - a*b. Quadratic constraints
    // allow only one multiplication, so the product needs its own signal.
    signal both;
    both <== not_required.out * is_met.out;
    deductible_valid <== not_required.out + is_met.out - both;
}

// Only these three are public. age, diagnosis_code_hash and deductible_met
// remain private witnesses.
component main {public [min_age, approved_diagnosis_hash, deductible_required]} = PatientCriteria();
