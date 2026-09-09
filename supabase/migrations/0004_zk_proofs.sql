-- Pavo Cloud — Phase 4: zero-knowledge proofs
-- Apply after 0003_appeals_identity.sql.

create extension if not exists "pgcrypto";

create table if not exists zk_proofs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_request_id UUID REFERENCES auth_requests(id),
  criteria JSONB,
  proof TEXT,
  public_signals JSONB,
  verified BOOLEAN,
  generated_at TIMESTAMPTZ DEFAULT now()
);

create index if not exists zk_proofs_auth_request_id_idx on zk_proofs (auth_request_id);
create index if not exists zk_proofs_generated_at_idx on zk_proofs (generated_at desc);
