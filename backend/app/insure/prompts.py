"""Prompts for the Insure document parser and CPT mapper.

The card, EOC, and CPT prompts are fixed by the Phase 2 specification and are
reproduced here verbatim. Do not reword them without updating the spec.
"""

CARD_SYSTEM_PROMPT = """You are a healthcare insurance document parser. Extract the following fields 
from the provided insurance card image and return valid JSON only. No explanation.

Fields:
- plan_name
- insurance_company
- group_number
- member_id
- network_name

If a field is not found, return null. Return JSON only."""


EOC_SYSTEM_PROMPT = """You are a healthcare insurance document parser. Extract the following fields 
from the provided Evidence of Coverage document and return valid JSON only. No explanation.

Fields:
- deductible_individual
- deductible_family
- deductible_met
- out_of_pocket_max_individual
- out_of_pocket_max_family
- primary_care_copay
- specialist_copay
- er_copay
- coinsurance_percentage
- covered_services (array of strings)
- prior_auth_required_for (array of strings)

If a field is not found, return null. Return JSON only."""


CPT_PROMPT_TEMPLATE = """Map this procedure description to the most likely CPT code. 
Return JSON only: {{"cpt_code": "XXXXX", "procedure_name": "Official name"}}
Procedure: {procedure_name}"""


# Fields each parser is expected to return, used to normalize a response that
# omits keys entirely.
CARD_FIELDS = (
    "plan_name",
    "insurance_company",
    "group_number",
    "member_id",
    "network_name",
)

EOC_FIELDS = (
    "deductible_individual",
    "deductible_family",
    "deductible_met",
    "out_of_pocket_max_individual",
    "out_of_pocket_max_family",
    "primary_care_copay",
    "specialist_copay",
    "er_copay",
    "coinsurance_percentage",
    "covered_services",
    "prior_auth_required_for",
)
