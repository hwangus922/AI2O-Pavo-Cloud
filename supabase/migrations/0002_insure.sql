-- Pavo Cloud — Phase 2 (Insure) schema
-- Apply after 0001_init.sql.

create extension if not exists "pgcrypto";

-- --------------------------------------------------------------- price_queries
create table if not exists price_queries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id TEXT,
  procedure_name TEXT,
  cpt_code TEXT,
  insurance_plan JSONB,
  results JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ---------------------------------------------------------- insurance_documents
create table if not exists insurance_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id TEXT,
  card_image_url TEXT,
  eoc_url TEXT,
  parsed_plan JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------- indexes
create index if not exists price_queries_created_at_idx on price_queries (created_at desc);
create index if not exists price_queries_member_id_idx on price_queries (member_id);
create index if not exists insurance_documents_created_at_idx on insurance_documents (created_at desc);
create index if not exists insurance_documents_member_id_idx on insurance_documents (member_id);
