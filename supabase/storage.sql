-- Storage bucket for Insure uploads (insurance cards and EOC PDFs).
-- Run once, alongside the migrations.

insert into storage.buckets (id, name, public)
values ('insure-documents', 'insure-documents', false)
on conflict (id) do nothing;
