-- Pavo Cloud — Phase 1 core schema
-- Apply with: supabase db push, or paste into the Supabase SQL editor.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------- organizations
create table if not exists organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT,
  type TEXT CHECK (type IN ('provider', 'payer', 'employer')),
  npi TEXT,
  payer_id TEXT,
  public_key TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------- auth_requests
create table if not exists auth_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_org_id UUID REFERENCES organizations(id),
  payer_org_id UUID REFERENCES organizations(id),
  patient_id TEXT,
  procedure_code TEXT,
  diagnosis_code TEXT,
  fhir_bundle JSONB,
  status TEXT CHECK (status IN ('pending', 'approved', 'denied', 'escalated', 'appealed')),
  decision_rule_id TEXT,
  confidence FLOAT,
  created_at TIMESTAMPTZ DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

-- ------------------------------------------------------------- aria_messages
create table if not exists aria_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id TEXT UNIQUE,
  auth_request_id UUID REFERENCES auth_requests(id),
  sender_agent_id TEXT,
  receiver_agent_id TEXT,
  payload_type TEXT,
  payload JSONB,
  signature TEXT,
  verified BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ----------------------------------------------------------------- audit_log
create table if not exists audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type TEXT,
  entity_id UUID,
  action TEXT,
  actor_agent_id TEXT,
  before_state JSONB,
  after_state JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------- indexes
create index if not exists auth_requests_created_at_idx on auth_requests (created_at desc);
create index if not exists auth_requests_status_idx on auth_requests (status);
create index if not exists aria_messages_auth_request_id_idx on aria_messages (auth_request_id);
create index if not exists aria_messages_created_at_idx on aria_messages (created_at);
create index if not exists audit_log_entity_idx on audit_log (entity_type, entity_id);
create index if not exists audit_log_created_at_idx on audit_log (created_at);
