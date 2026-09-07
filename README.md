# AI2O-Pavo-Cloud

Pavo Cloud eliminates prior authorization delays by enabling AI agents to handle the entire approval process autonomously. Provider and payer agents communicate directly via FHIR, resolving clear cases in under 5 minutes — cutting the 3-14 day wait and $35B in annual admin waste.

**Phase 1 (the core loop) is implemented and runnable.** The full product specification lives in [`docs/pavo_cloud_build.md`](docs/pavo_cloud_build.md).

---

## What Phase 1 does

An order placed in an EHR fires a webhook. From there no human touches the request:

1. The **Provider Agent** assembles a FHIR R4 bundle (Patient, Condition, ServiceRequest) from the order.
2. It sends a signed **ARIA** `AUTH_REQUEST` to the payer.
3. The **Payer Agent** verifies the signature and runs the bundle through a deterministic **rule engine**.
4. The decision, the rule that produced it, and every message are written to the **audit log**.
5. An `AUTH_RESPONSE` returns the outcome.

Clear cases resolve automatically. Ambiguous ones are marked `escalated` for a human reviewer with the whole record already assembled.

## Repository layout

| Path | What lives there |
|---|---|
| `backend/` | FastAPI service: agents, rule engine, ARIA protocol, persistence |
| `frontend/` | Next.js 14 App Router dashboard with Clerk authentication |
| `supabase/` | Schema migration and demo seed data |
| `docs/` | Full build specification |

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
| `GET` | `/api/auth` | List authorization requests, newest first. |
| `GET` | `/api/auth/{id}` | One request with its ARIA thread and audit trail. |
| `POST` | `/api/aria/receive` | Payer endpoint for inbound ARIA messages. |
| `POST` | `/api/aria/verify` | Verify an envelope signature without acting on it. |
| `GET` | `/api/audit/{entity_id}` | Full audit trail for any entity. |
| `GET` | `/api/rules` | The active coverage rules. |
| `GET` | `/health` | Liveness, plus which storage backend is active. |

## Database

Apply the schema in `supabase/migrations/0001_init.sql`, then optionally seed the demo provider and payer with `supabase/seed.sql`. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env` and the service switches from the in-memory store to Supabase with no other changes.

## Tests

```bash
cd backend && .venv/bin/python -m pytest
```

29 tests cover all five rules, rule precedence, code normalization, patient-ID hashing, the end-to-end webhook flow, ARIA signing and tamper detection, and the audit trail.

## Configuration

Copy `.env.example` to `.env`. `backend/.env.example` and `frontend/.env.local.example` carry the per-service subsets.

| Variable | Used by | Notes |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | backend | Omit both to run in memory |
| `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` | frontend | Reserved for direct browser reads |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY` | frontend | Omit to leave routes public |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | Defaults to `http://localhost:8000` |
| `ANTHROPIC_API_KEY` | backend | Unused in Phase 1; reserved for appeals |
| `ARIA_VERSION` | backend | Defaults to `1.0` |

## Operating constraints

These hold in code, not just on paper:

- **Raw PHI is never stored.** Patient identifiers are SHA-256 hashed before they reach the database.
- **Every decision carries a `rule_id`.** The rule engine cannot return an outcome without one, and it is written to `audit_log` on every decision.
- **Ambiguity escalates.** Anything without a definitive rule match becomes `escalated` rather than being guessed at.

## What is not built yet

Phases 2 through 4 of the specification remain open: the Insure price-transparency product, autonomous appeals, federated learning, and zero-knowledge proofs. ARIA signing currently uses a shared demo HMAC secret; per-organization key pairs and live NPI verification against the CMS registry are Phase 3.
