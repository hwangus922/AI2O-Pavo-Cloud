# Pavo Cloud — Full Build Specification
*Internal Technical Reference | Prototype v1*

---

## Overview

Pavo Cloud is the end-to-end operating system for autonomous healthcare financial transactions. It removes human bottlenecks from every step of the process — from insurance authorization to real-time price transparency — using a network of specialized AI agents communicating over **ARIA** (Autonomous Request and Intelligence Architecture), Pavo's proprietary agent protocol.

**Two products, one infrastructure:**
- **Pavo Core** — B2B infrastructure: autonomous prior authorization between provider and payer AI agents
- **Insure** — B2B2C consumer layer: voice agents that parse insurance documents and phone lines to deliver real-time price transparency, sold through employers

---

## Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | Next.js 14 (App Router) | SSR, API routes, file upload handling |
| Backend | Python (FastAPI) | Async, LLM-friendly, strong healthcare library support |
| LLM | Claude claude-sonnet-4-6 (Anthropic) | Best for long document parsing, instruction following |
| Voice | Vapi | Best-in-class for outbound voice agents, function calling support |
| Agent Framework | LangGraph | Stateful multi-agent orchestration, human-in-the-loop support |
| Database | PostgreSQL (Supabase) | Structured clinical data, audit trails |
| Auth | Clerk | Fast to implement, enterprise SSO ready |
| File Storage | Supabase Storage | HIPAA-eligible, integrated with DB |
| Encryption | AES-256 + TLS 1.3 | Data at rest and in transit |
| FHIR | HAPI FHIR (Java) or medplum (Node) | CMS-0057-F compliant |
| Deployment | Vercel (frontend) + Railway (backend) | Fast iteration |

---

## ARIA Protocol

ARIA is the agent communication standard that all Pavo Cloud products run on. It defines how autonomous AI agents identify themselves, exchange clinical data, and reach decisions across organizational boundaries.

### Core Principles
- **No human required to initiate** — agents wake up on system events, not staff actions
- **Every decision traces to a rule** — no black box outputs
- **Ambiguity escalates** — the system knows what it doesn't know
- **Full audit trail** — every message, every decision, timestamped and immutable

### ARIA Message Structure
```json
{
  "aria_version": "1.0",
  "message_id": "uuid",
  "timestamp": "ISO8601",
  "sender": {
    "agent_id": "string",
    "org_id": "string",
    "npi": "string",
    "verified": true
  },
  "receiver": {
    "agent_id": "string",
    "org_id": "string",
    "payer_id": "string"
  },
  "payload_type": "AUTH_REQUEST | AUTH_RESPONSE | APPEAL | PRICE_QUERY | PRICE_RESPONSE",
  "payload": {},
  "signature": "cryptographic_hash"
}
```

### Identity Verification
- Sender NPI verified live against CMS enrollment API
- Payer ID verified against CMS payer registry
- Message signed with org-level key pair
- Signature verified before payload is processed

---

## Product 1: Pavo Core (Prior Authorization)

### User Flow
1. Physician enters treatment order in EHR
2. EHR webhook fires to Pavo Core API
3. Provider agent assembles FHIR bundle from patient chart
4. Provider agent sends ARIA `AUTH_REQUEST` to payer agent
5. Payer agent verifies identity, pulls clinical coverage rules
6. Deterministic rule engine evaluates request
7. Clear cases: auto-approved, decision returned in < 5 min
8. Ambiguous cases: ML classifier flags for human reviewer with full context pre-loaded
9. Decision + audit trail written to database
10. EHR updated automatically

### Agents

#### Provider Agent
```
Role: Assemble and submit authorization requests on behalf of providers
Triggers: EHR webhook (new order)
Inputs: Patient chart, procedure code, diagnosis code, provider NPI
Outputs: FHIR R4 bundle, ARIA AUTH_REQUEST message
Tools: EHR read API, FHIR validator, ARIA send
```

#### Payer Agent
```
Role: Evaluate authorization requests against coverage rules
Triggers: Incoming ARIA AUTH_REQUEST
Inputs: FHIR bundle, payer coverage criteria (published, scraped on intake)
Outputs: ARIA AUTH_RESPONSE (approved / denied / escalate)
Tools: Coverage rules DB, deterministic rule engine, ML classifier, ARIA send
```

#### Escalation Agent
```
Role: Prepare ambiguous cases for human reviewer
Triggers: ML classifier confidence < threshold
Inputs: Full ARIA message thread, patient context, relevant coverage rules
Outputs: Pre-populated reviewer dashboard with recommended decision and supporting evidence
Tools: Case summarizer, evidence retriever, reviewer notification
```

### Rule Engine Logic
```python
def evaluate_request(fhir_bundle, coverage_rules):
    procedure = extract_procedure(fhir_bundle)
    diagnosis = extract_diagnosis(fhir_bundle)
    
    # Check hard rules first (deterministic)
    hard_result = check_hard_rules(procedure, diagnosis, coverage_rules)
    if hard_result.is_definitive:
        return Decision(
            outcome=hard_result.outcome,
            rule_id=hard_result.rule_id,
            confidence=1.0
        )
    
    # Ambiguous — send to ML classifier
    confidence = ml_classifier.predict(fhir_bundle, coverage_rules)
    if confidence < THRESHOLD:
        return Decision(outcome="ESCALATE", confidence=confidence)
    
    return Decision(outcome=hard_result.outcome, confidence=confidence)
```

---

## Product 2: Insure (Price Transparency)

### User Flow
1. User uploads photo of insurance card + Evidence of Coverage (EOC) document
2. Document parsing agent extracts: plan name, group number, member ID, deductible, OOP max, copay/coinsurance structure
3. User speaks or types the procedure they need ("I need an MRI of my knee")
4. Voice agent calls top local facilities to get real negotiated rates and cash prices
5. Insure builds ranked list: cost (insurance rate vs. cash price), proximity, quality score
6. User sees full breakdown — which option is actually cheapest for them given their deductible status

### Agents

#### Document Parser Agent
```
Role: Extract structured insurance data from uploaded documents
Triggers: File upload event
Inputs: Insurance card image (JPG/PNG), EOC PDF
Outputs: Structured JSON — plan details, cost-sharing structure, covered services
Tools: Claude vision (card OCR), Claude document parsing (EOC), FHIR coverage resource
Model: claude-sonnet-4-6 with vision
```

#### Voice Agent (Vapi)
```
Role: Call insurance companies and facilities to get real-time pricing
Triggers: User procedure query
Inputs: Procedure name, CPT code, facility phone numbers, member insurance details
Outputs: Negotiated rate, cash price, availability
Tools: Vapi outbound call, CPT code lookup, phone number resolver
Personality: Professional, efficient, never on hold longer than 8 min (auto-retry)
Script: Dynamic — generated per call based on insurance plan and procedure
```

#### Ranking Agent
```
Role: Build ranked facility list from pricing data
Triggers: Voice agent returns pricing data
Inputs: Negotiated rates, cash prices, user deductible status, facility coordinates, CMS quality scores
Outputs: Ranked list with cost breakdown (what user actually pays given deductible)
Logic:
  - If deductible not met: compare cash price vs. insurance rate + coinsurance
  - If deductible met: insurance rate + coinsurance only
  - Quality score from CMS Hospital Compare / Leapfrog
  - Distance from user zip
```

### Document Parsing Prompt (Claude)
```
You are a healthcare insurance document parser. Extract the following fields 
from the provided document and return valid JSON only.

Fields to extract:
- plan_name
- insurance_company  
- group_number
- member_id
- deductible_individual (annual)
- deductible_family (annual)
- deductible_met (if stated)
- out_of_pocket_max_individual
- out_of_pocket_max_family
- primary_care_copay
- specialist_copay
- er_copay
- coinsurance_percentage
- covered_services (array)
- network_name
- prior_auth_required_for (array of procedure types)

If a field is not found, return null. Never guess.
Return JSON only, no explanation.
```

---

## Product 3: Autonomous Appeals

### Overview
When Pavo Core receives a denial, the Appeals Agent automatically generates a clinical appeal, pulls supporting medical literature, and resubmits — without human involvement for standard denial reasons.

### Flow
1. Payer agent returns `AUTH_RESPONSE` with `outcome: DENIED`
2. Denial classifier categorizes reason (medical necessity, not covered, missing info)
3. Appeals agent retrieves relevant clinical guidelines (CMS, specialty society)
4. LLM drafts appeal letter citing specific guidelines and patient-specific evidence
5. Appeal submitted via ARIA `APPEAL` message
6. If second denial: escalates to human with full appeal history pre-loaded

### Appeals Agent
```
Role: Generate and submit clinical appeals for denied authorizations
Triggers: AUTH_RESPONSE with outcome=DENIED
Inputs: Original FHIR bundle, denial reason code, payer coverage policy
Outputs: Formatted appeal letter, ARIA APPEAL message
Tools: 
  - PubMed API (clinical evidence retrieval)
  - CMS guidelines database
  - Appeal letter generator (Claude)
  - ARIA send
Constraint: Never submit an appeal the system has < 70% confidence in — escalate instead
```

---

## Product 4: Federated Learning Layer

### Overview
Every authorization decision is a training signal. Pavo aggregates outcomes across all payer networks using federated learning — improving the ML classifier without any single entity owning patient data.

### Architecture
- Each payer node trains locally on its own decision data
- Only model gradients (not raw data) are shared with Pavo central server
- Central server aggregates gradients using FedAvg algorithm
- Updated global model distributed back to all nodes
- Differentially private — individual patient data cannot be reconstructed

### What It Learns
- Which procedure + diagnosis combinations get approved by which payers
- Which clinical documentation patterns lead to faster approvals
- Which denial reasons are successfully appealed and why
- Regional variation in coverage decisions

### Privacy Guarantee
- No raw PHI ever leaves the payer node
- Differential privacy noise added before gradient sharing
- Audit log of all model updates
- HIPAA Business Associate Agreement required for all nodes

---

## Product 5: Zero-Knowledge Proofs for PHI

### Overview
Instead of sharing raw patient data in ARIA messages, Pavo uses ZK proofs to prove that clinical criteria are satisfied without revealing the underlying data.

### Use Case
Payer needs to verify: "Does this patient have a diagnosis of X and have failed conservative treatment Y?"

Instead of sending the patient record, the provider agent generates a ZK proof that:
- Patient has diagnosis matching ICD-10 code Z87.891 ✓
- Patient has documented trial of conservative treatment ✓
- Patient meets age criteria ✓

Payer verifies the proof without seeing any PHI.

### Implementation
- Library: snarkjs (JavaScript) or arkworks (Rust)
- Circuit: Custom per payer coverage criteria
- Proof generation: Provider agent (local)
- Proof verification: Payer agent
- Fallback: Full FHIR bundle for cases where ZK circuit not yet defined

> **Note:** ZK proof circuit generation per payer criteria is the hardest engineering problem in this stack. Prototype will use simplified circuits for 2-3 common criteria. Full implementation is Year 2.

---

## Database Schema (Core Tables)

```sql
-- Organizations
CREATE TABLE organizations (
  id UUID PRIMARY KEY,
  name TEXT,
  type TEXT CHECK (type IN ('provider', 'payer', 'employer')),
  npi TEXT,
  payer_id TEXT,
  public_key TEXT,
  created_at TIMESTAMPTZ
);

-- Authorization Requests
CREATE TABLE auth_requests (
  id UUID PRIMARY KEY,
  provider_org_id UUID REFERENCES organizations(id),
  payer_org_id UUID REFERENCES organizations(id),
  patient_id TEXT, -- hashed
  procedure_code TEXT,
  diagnosis_code TEXT,
  fhir_bundle JSONB,
  status TEXT CHECK (status IN ('pending', 'approved', 'denied', 'escalated', 'appealed')),
  decision_rule_id TEXT,
  confidence FLOAT,
  created_at TIMESTAMPTZ,
  resolved_at TIMESTAMPTZ
);

-- ARIA Messages
CREATE TABLE aria_messages (
  id UUID PRIMARY KEY,
  message_id TEXT UNIQUE,
  auth_request_id UUID REFERENCES auth_requests(id),
  sender_agent_id TEXT,
  receiver_agent_id TEXT,
  payload_type TEXT,
  payload JSONB,
  signature TEXT,
  verified BOOLEAN,
  created_at TIMESTAMPTZ
);

-- Price Queries (Insure)
CREATE TABLE price_queries (
  id UUID PRIMARY KEY,
  employer_id UUID REFERENCES organizations(id),
  member_id TEXT, -- hashed
  procedure_name TEXT,
  cpt_code TEXT,
  insurance_plan JSONB,
  results JSONB, -- ranked facility list
  created_at TIMESTAMPTZ
);

-- Audit Trail
CREATE TABLE audit_log (
  id UUID PRIMARY KEY,
  entity_type TEXT,
  entity_id UUID,
  action TEXT,
  actor_agent_id TEXT,
  before_state JSONB,
  after_state JSONB,
  created_at TIMESTAMPTZ
);
```

---

## API Routes

```
POST /api/auth/request          — Provider submits new auth request
GET  /api/auth/:id              — Get auth request status
POST /api/auth/:id/appeal       — Trigger appeal on denial
POST /api/aria/receive          — Payer endpoint for incoming ARIA messages
POST /api/insure/parse          — Upload insurance documents
POST /api/insure/query          — Submit procedure price query
GET  /api/insure/results/:id    — Get ranked facility list
POST /api/aria/verify           — Verify ARIA message signature
GET  /api/audit/:entity_id      — Get full audit trail for any entity
```

---

## Prototype Build Order

Build in this sequence — each phase is demoable on its own.

### Phase 1 — Core Loop (Week 1-2)
- [ ] Supabase setup (schema above)
- [ ] FastAPI backend with core routes
- [ ] Mock EHR webhook → Provider Agent → FHIR bundle assembly
- [ ] Deterministic rule engine (hardcode 5 common procedure rules)
- [ ] Mock Payer Agent response
- [ ] Basic Next.js dashboard showing request → decision flow
- [ ] ARIA message logging

### Phase 2 — Insure MVP (Week 2-3)
- [ ] File upload UI (insurance card + EOC)
- [ ] Claude vision integration for card parsing
- [ ] Claude document parsing for EOC PDF
- [ ] CPT code lookup from procedure name
- [ ] Vapi voice agent setup (outbound call to mock facility)
- [ ] Ranking algorithm
- [ ] Results UI with cost breakdown

### Phase 3 — Appeals + Identity (Week 3-4)
- [ ] Denial classifier
- [ ] PubMed API integration
- [ ] Appeal letter generation (Claude)
- [ ] Cryptographic identity verification (key pairs per org)
- [ ] ARIA message signing and verification

### Phase 4 — Polish for Demo (Week 4)
- [ ] End-to-end demo flow: EHR trigger → auth → price check → appeal
- [ ] Audit trail UI
- [ ] ZK proof demo (simplified single criterion)
- [ ] Federated learning diagram / mock (actual FL is post-prototype)

---

## Environment Variables

```env
# Anthropic
ANTHROPIC_API_KEY=

# Supabase
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Vapi
VAPI_API_KEY=
VAPI_PHONE_NUMBER_ID=

# CMS APIs
CMS_NPI_REGISTRY_URL=https://npiregistry.cms.hhs.gov/api
CMS_PAYER_REGISTRY_URL=

# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=

# FHIR
FHIR_SERVER_URL=

# App
ARIA_VERSION=1.0
ML_CLASSIFIER_THRESHOLD=0.75
APPEAL_CONFIDENCE_THRESHOLD=0.70
```

---

## Key Constraints

- **Never store raw PHI** — hash all patient identifiers, encrypt everything else
- **Every denial goes to a human** — no automated final denials
- **Every decision has a rule_id** — no black box outputs in production
- **HIPAA BAA required** before any real data flows through the system
- **ZK proofs and federated learning are roadmap** — prototype uses simplified mocks for demo purposes

---

*Pavo Cloud | ARIA Protocol v1.0 | Built for AI Innovation Olympiad Finals*
