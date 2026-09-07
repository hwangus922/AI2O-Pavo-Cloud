-- Demo organizations: one provider, one payer.
-- The backend falls back to these fixed UUIDs so a fresh database is demoable.

insert into organizations (id, name, type, npi, payer_id, public_key)
values (
  '11111111-1111-4111-8111-111111111111',
  'Metro Valley Health Network',
  'provider',
  '1598765432',
  null,
  'demo-provider-public-key'
)
on conflict (id) do nothing;

insert into organizations (id, name, type, npi, payer_id, public_key)
values (
  '22222222-2222-4222-8222-222222222222',
  'Meridian Health Plan',
  'payer',
  null,
  'MERIDIAN-001',
  'demo-payer-public-key'
)
on conflict (id) do nothing;
