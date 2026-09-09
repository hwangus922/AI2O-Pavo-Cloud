-- Pavo Cloud — Phase 3: appeals and cryptographic identity
-- Apply after 0002_insure.sql.

create extension if not exists "pgcrypto";

-- --------------------------------------------------------------------- appeals
create table if not exists appeals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_request_id UUID REFERENCES auth_requests(id),
  denial_reason_code TEXT,
  denial_reason_category TEXT CHECK (denial_reason_category IN ('medical_necessity', 'not_covered', 'missing_info', 'other')),
  appeal_letter TEXT,
  pubmed_citations JSONB,
  confidence FLOAT,
  status TEXT CHECK (status IN ('draft', 'submitted', 'won', 'lost', 'escalated')),
  created_at TIMESTAMPTZ DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

-- -------------------------------------------------------------------- org_keys
-- Only public keys are stored. private_key_hash is a SHA-256 digest of the
-- private key, held so an organization can prove which key it controls; the
-- private key itself is returned once at creation and never persisted.
create table if not exists org_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES organizations(id),
  public_key TEXT NOT NULL,
  private_key_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  revoked_at TIMESTAMPTZ
);

-- -------------------------------------------------------------------- indexes
create index if not exists appeals_auth_request_id_idx on appeals (auth_request_id);
create index if not exists appeals_status_idx on appeals (status);
create index if not exists appeals_created_at_idx on appeals (created_at desc);
create index if not exists org_keys_org_id_idx on org_keys (org_id);
-- One active key per organization.
create unique index if not exists org_keys_active_org_idx
  on org_keys (org_id) where revoked_at is null;
