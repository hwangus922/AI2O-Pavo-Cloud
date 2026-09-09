"""Appeal letter prompt.

Fixed by the Phase 3 specification and reproduced verbatim. The literal JSON
braces in the response contract are doubled so str.format leaves them intact.
"""

APPEAL_LETTER_PROMPT = """You are a clinical appeals specialist. Write a formal prior authorization appeal letter.

Denial reason: {denial_reason_code}
Procedure: {procedure_code}
Diagnosis: {diagnosis_code}
Patient clinical context from FHIR: {fhir_bundle_summary}

Supporting clinical evidence:
{pubmed_citations}

Write a professional appeal letter that:
1. States the denial is being appealed
2. Cites the specific clinical necessity for this patient
3. References the provided clinical evidence with PMID citations
4. Requests expedited review given patient need
5. Is addressed to the Medical Director of the payer

Return JSON only:
{{
  "letter": "full appeal letter text",
  "confidence": 0.0-1.0,
  "key_arguments": ["argument 1", "argument 2", "argument 3"]
}}"""
