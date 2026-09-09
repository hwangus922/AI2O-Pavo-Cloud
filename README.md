# AI2O-Pavo-Cloud

Pavo Cloud eliminates prior authorization delays by enabling AI agents to handle the entire approval process autonomously. Provider and payer agents communicate directly via FHIR, resolving clear cases in under 5 minutes — cutting the 3-14 day wait and $35B in annual admin waste.

**All four phases are implemented and runnable.** The full product specification lives in [`docs/pavo_cloud_build.md`](docs/pavo_cloud_build.md).

---

## What Phase 1 does

An order placed in an EHR fires a webhook. From there no human touches the request:

1. The **Provider Agent** assembles a FHIR R4 bundle (Patient, Condition, ServiceRequest) from the order.
2. It sends a signed **ARIA** `AUTH_REQUEST` to the payer.
3. The **Payer Agent** verifies the signature and runs the bundle through a deterministic **rule engine**.
4. The decision, the rule that produced it, and every message are written to the **audit log**.
5. An `AUTH_RESPONSE` returns the outcome.

Clear cases resolve automatically. Ambiguous ones are marked `escalated` for a human reviewer with the whole record already assembled.

## What Phase 2 does (Insure)

Insure is the consumer-facing price transparency layer, at `/insure`:

1. A member uploads their **insurance card** (JPG/PNG) and **Evidence of Coverage** (PDF).
2. Claude reads the card with vision and the EOC as a document, and the two results merge into one `insurance_plan`.
3. The member types the procedure they need in plain language.
4. Claude maps that to a **CPT code**, and Insure prices it at five facilities.
5. Results are ranked by **what the member actually pays**, with a badge showing whether insurance or cash is cheaper and a toggle revealing the arithmetic.

Uploads land in the `insure-documents` bucket. Every query writes to `audit_log` with `entity_type='price_query'`.

## What Phase 3 does (appeals and identity)

**Cryptographic identity.** Every organization gets an RSA-2048 key pair. The public key is stored in `org_keys` and on the organization record; the private key is returned once at creation and never persisted — only a SHA-256 digest of it is kept. Every ARIA message is signed over the SHA-256 digest of its contents (RSASSA-PSS) and verified against the sender's registered public key. A message that fails verification is rejected with a 401 and the rejection is written to the audit log.

**Autonomous appeals.** When an authorization is denied:

1. The denial reason is classified as `medical_necessity`, `not_covered`, `missing_info`, or `other`.
2. A `not_covered` denial is never appealed automatically — coverage is a contract question, so it escalates to a human with no letter drafted.
3. Otherwise the agent searches PubMed for supporting evidence, fetches the top three abstracts, and asks Claude to draft an appeal letter with PMID citations.
4. At or above 0.70 confidence the appeal is submitted to the payer over a signed ARIA `APPEAL` message. Below it, the appeal is stored as `escalated` with pre-populated reviewer notes.
5. The payer agent verifies the signature and decides. A rejected appeal escalates to a human — it never becomes an automated final denial.

## The 30-second demo

`/demo` walks the entire product in one page, driven by live data. Press
**Run Full Demo** and it advances through six steps with no further input:

| Step | What it shows |
|---|---|
| 1. EHR trigger | The order, the FHIR bundle, and the ARIA envelope being built |
| 2. Identity | Both signatures verified against registered public keys |
| 3. Zero-knowledge | Three patient criteria proven without revealing the data |
| 4. Rule engine | The deterministic rule that fired, with its ID |
| 5. Decision | The outcome and the full audit trail behind it |
| 6. Insure | The same procedure priced across five facilities |

A measured run completes in about **11 seconds**. Each step also has a
**Next** button for a manual walkthrough, and a failed step shows a retry
rather than a broken page.

### Presenting it

```bash
# 1. Backend
cd backend && .venv/bin/uvicorn app.main:app --port 8000

# 2. Seed a populated demo (optional but recommended)
python scripts/seed_demo.py

# 3. Frontend
cd frontend && npm run dev
```

Then open `http://localhost:3000/demo`. `/audit` shows every event across the
system with filters and CSV export; `/dashboard` shows live counters and an
ARIA message feed.

If you serve the frontend on a port other than 3000, set `FRONTEND_ORIGIN`
on the backend to that origin or the browser will block the calls.

## Repository layout

| Path | What lives there |
|---|---|
| `backend/` | FastAPI service: agents, rule engine, ARIA protocol, persistence |
| `frontend/` | Next.js 14 App Router dashboard with Clerk authentication |
| `supabase/` | Schema migration and demo seed data |
| `docs/` | Full build specification |
| `circuits/` | The `patient_criteria` circom circuit |
| `zk/` | snarkjs workspace, build script, and compiled artifacts |
| `scripts/` | `seed_demo.py`, which populates a demo dataset |

## Quick start

The backend runs on an in-memory store when Supabase credentials are absent, so you can see the whole loop working before configuring anything.

### 1. Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

The API is now on `http://localhost:8000`, with interactive docs at `/docs`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # optional: fill in Clerk keys
npm run dev
```

Open `http://localhost:3000/dashboard`.

Clerk is optional for local work. Without a publishable key the app still boots and every route stays public; add the key and the dashboard routes become protected.

### 3. Try the loop

```bash
curl -X POST http://localhost:8000/api/auth/request \
  -H 'Content-Type: application/json' \
  -d '{"procedure_code":"27447","diagnosis_code":"M17.11"}'
```

## Zero-knowledge proofs

`circuits/patient_criteria.circom` proves three things to a payer without
disclosing the data behind them:

- the patient meets the age floor — the age is never sent
- the diagnosis matches the covered condition — the code is never sent
- the deductible requirement is satisfied — no amount is ever sent

The artifacts are committed, so proving works out of the box. To rebuild:

```bash
# circom is a Rust binary and is not on npm
git clone https://github.com/iden3/circom && cd circom && cargo build --release
export CIRCOM=$PWD/target/release/circom

cd /path/to/AI2O-Pavo-Cloud/zk && npm install && bash build.sh
```

## Coverage rules

Five deterministic rules ship in Phase 1. They are evaluated in order and the first match wins, so the specific knee rule is checked before the general one.

| Rule | Procedure | Diagnosis | Outcome |
|---|---|---|---|
| `PAVO-R001` | 70553 (MRI brain) | any | APPROVED |
| `PAVO-R002` | 27447 (knee replacement) | M17.11 | APPROVED |
| `PAVO-R003` | 27447 (knee replacement) | any other | ESCALATED |
| `PAVO-R004` | 99214 (office visit) | any | APPROVED |
| `PAVO-R005` | any other | any | ESCALATED |

`GET /api/rules` returns this table at runtime.

## API

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/auth/request` | Mock EHR webhook. Submits an order and returns the decision. |
| `GET` | `/api/auth` | List authorization requests, newest first. Filter with `?status=`. |
| `GET` | `/api/auth/{id}` | One request with its ARIA thread and audit trail. |
| `POST` | `/api/aria/receive` | Payer endpoint for inbound ARIA messages. |
| `POST` | `/api/aria/verify` | Verify an envelope signature without acting on it. |
| `GET` | `/api/audit/{entity_id}` | Full audit trail for any entity. |
| `GET` | `/api/rules` | The active coverage rules. |
| `POST` | `/api/auth/{id}/appeal` | Generate an appeal for a denied request. |
| `GET` | `/api/appeals` | List appeals, newest first. |
| `GET` | `/api/appeals/stats` | Appeal counts and win rate. |
| `GET` | `/api/appeals/{id}` | Retrieve one appeal. |
| `POST` | `/api/insure/parse` | Upload a card and EOC; returns the merged plan. |
| `POST` | `/api/insure/query` | Price a procedure and rank facilities. |
| `GET` | `/api/insure/results/{id}` | Retrieve a stored price query. |
| `GET` | `/api/insure/queries` | List price queries, newest first. |
| `POST` | `/api/zk/generate` | Prove the patient criteria; returns proof and public signals. |
| `POST` | `/api/zk/verify` | Verify a proof against the circuit's verification key. |
| `GET` | `/api/zk/status` | Whether the circuit artifacts are built. |
| `GET` | `/api/system/stats` | Live counters for the dashboard. |
| `GET` | `/api/system/activity` | The most recent ARIA messages. |
| `GET` | `/api/system/audit` | The whole audit trail, filterable. |
| `GET` | `/health` | Liveness, plus which backends are active. |

## Database

Apply the migrations in `supabase/migrations/` in order (`0001_init.sql`, `0002_insure.sql`, `0003_appeals_identity.sql`, `0004_zk_proofs.sql`), create the storage bucket with `supabase/storage.sql`, then optionally seed the demo provider and payer with `supabase/seed.sql`. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env` and the service switches from the in-memory store to Supabase with no other changes.

## Tests

```bash
cd backend && .venv/bin/python -m pytest
```

129 tests cover all four phases: the five coverage rules and their precedence, identifier hashing, the end-to-end webhook flow, RSA signing and tamper rejection, the audit trail, document upload and validation, CPT mapping, the cash-vs-insurance price bands, every branch of the ranking algorithm, denial classification, PubMed parsing against recorded fixtures, each appeal outcome path, the ZK circuit end to end (real proofs, every criterion branch, tamper rejection, and the guarantee that private inputs never reach the response), and the system statistics.

## Configuration

Copy `.env.example` to `.env`. `backend/.env.example` and `frontend/.env.local.example` carry the per-service subsets.

| Variable | Used by | Notes |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | backend | Omit both to run in memory |
| `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` | frontend | Reserved for direct browser reads |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY` | frontend | Omit to leave routes public |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | Defaults to `http://localhost:8000`; inlined at build time |
| `FRONTEND_ORIGIN` | backend | Comma-separated CORS allowlist; add your origin if not on port 3000 |
| `ANTHROPIC_API_KEY` | backend | Insure parsing and CPT mapping; unset yields labelled sample data |
| `ARIA_VERSION` | backend | Defaults to `1.0` |

## Operating constraints

These hold in code, not just on paper:

- **Raw PHI is never stored.** Patient identifiers are SHA-256 hashed before they reach the database.
- **Every decision carries a `rule_id`.** The rule engine cannot return an outcome without one, and it is written to `audit_log` on every decision.
- **Ambiguity escalates.** Anything without a definitive rule match becomes `escalated` rather than being guessed at.
- **Member identifiers are hashed too**, including the member ID read off an insurance card, and the hash — never the raw value — is what appears in storage paths.
- **Sample data is always labelled.** When `ANTHROPIC_API_KEY` is unset the parsers return obvious placeholder values, and the API response and the UI both say so. Nothing silently invents a member's plan.
- **No automated final denial.** A denial is either appealed or escalated to a human. The payer agent answers a rejected appeal with `ESCALATED`, never `DENIED`.
- **Private keys never reach the database.** `org_keys` stores the public key and a digest of the private key, nothing more.
- **Unverified messages do not act.** A signature that fails verification is rejected with a 401 before its payload is read, and the rejection is audited.

## Known limitations

Worth stating plainly before a demo:

- **The ZK circuit is deliberately simplified.** The approved-diagnosis check
  compares against a single hash, so a passing proof does tell the payer the
  patient carries that one diagnosis. Proving membership in a set of many
  codes without revealing which needs a Merkle circuit, which is out of scope
  here. The age and deductible criteria leak nothing.
- **The trusted setup is local.** `zk/build.sh` runs its own Powers of Tau
  ceremony, so whoever runs it knows the toxic waste. Fine for a prototype;
  never use these artifacts to secure anything real.
- **PubMed is unreachable from restricted networks.** Environments that
  block `eutils.ncbi.nlm.nih.gov` get zero citations; the appeal still
  completes and reports the lookup failure rather than falling over.
- **Facility pricing is mocked.** Prices are generated deterministically from
  the CPT code rather than gathered by the Vapi voice agent.
- **NPI verification is a flag, not a lookup** against the live CMS registry.
- **Federated learning is not built.**
- **Appeals need `ANTHROPIC_API_KEY`.** Without it the letter generator
  returns a clearly labelled placeholder scored 0.0, which is below the 0.70
  threshold — so every appeal escalates rather than being submitted. That is
  the intended safe default, not a failure.
- **The default backend stores everything in memory.** Data lives as long as
  the process; point it at Supabase for persistence.

### Where the demo agents keep their keys

In production an organization holds its own private key and signs before a message reaches Pavo. Here Pavo also *runs* the provider and payer agents, so those agents need a key to sign with. `backend/app/keyring.py` holds them in process memory only — never in the database, never on disk — and they are regenerated on every restart. That is a prototype accommodation, not a deployment pattern.

### A note on the pricing formulas

The ranking rules are implemented exactly as the Phase 2 specification defines them:

```
deductible not met -> min(cash_price, coinsurance x negotiated_rate)
deductible met     -> coinsurance x negotiated_rate
```

Both apply coinsurance regardless of deductible status, which is not how a real plan works — before the deductible is met a member normally owes the full negotiated rate, and coinsurance begins afterwards. One consequence is visible in the demo: at a typical 20% coinsurance the insurance path always beats the cash price, so the cash-is-cheaper case only appears at higher coinsurance. Changing this is a product decision; `estimate_member_cost` in `backend/app/insure/ranking.py` is the single place to make it.
