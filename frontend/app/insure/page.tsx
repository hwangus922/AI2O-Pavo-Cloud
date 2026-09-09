"use client";

import { useState } from "react";

import { FacilityCard } from "@/components/FacilityCard";
import { FileDropzone } from "@/components/FileDropzone";
import { PlanSummary } from "@/components/PlanSummary";
import { ApiError, parseInsuranceDocuments, submitPriceQuery } from "@/lib/api";
import type { ParsedDocumentResult, PriceQueryResult } from "@/lib/types";

const EXAMPLE_PROCEDURES = [
  "MRI of my knee",
  "MRI brain",
  "Colonoscopy",
  "Screening mammogram",
  "Knee replacement",
];

function errorMessage(caught: unknown, fallback: string): string {
  return caught instanceof ApiError ? caught.message : fallback;
}

export default function InsurePage() {
  const [cardImage, setCardImage] = useState<File | null>(null);
  const [eocPdf, setEocPdf] = useState<File | null>(null);
  const [memberId, setMemberId] = useState("");

  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [document, setDocument] = useState<ParsedDocumentResult | null>(null);

  const [procedure, setProcedure] = useState("");
  const [querying, setQuerying] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [priceQuery, setPriceQuery] = useState<PriceQueryResult | null>(null);

  const canUpload = Boolean(cardImage && eocPdf) && !parsing;

  async function handleParse(event: React.FormEvent) {
    event.preventDefault();
    if (!cardImage || !eocPdf) return;

    setParsing(true);
    setParseError(null);
    setPriceQuery(null);

    try {
      setDocument(
        await parseInsuranceDocuments({
          cardImage,
          eocPdf,
          memberId: memberId.trim() || undefined,
        })
      );
    } catch (caught) {
      setParseError(
        errorMessage(
          caught,
          "Could not reach the Pavo Cloud API. Is the backend running?"
        )
      );
    } finally {
      setParsing(false);
    }
  }

  async function handleQuery(event: React.FormEvent) {
    event.preventDefault();
    if (!document || !procedure.trim()) return;

    setQuerying(true);
    setQueryError(null);

    try {
      setPriceQuery(
        await submitPriceQuery({
          procedure_name: procedure.trim(),
          document_id: document.document_id,
        })
      );
    } catch (caught) {
      setQueryError(errorMessage(caught, "Could not price that procedure."));
    } finally {
      setQuerying(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-medium uppercase tracking-wide text-navy-400">
          Insure
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          Know what a procedure actually costs you
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-navy-600">
          Upload your insurance card and Evidence of Coverage. Insure reads your
          plan, then compares what you would pay at nearby facilities — through
          insurance or in cash.
        </p>
      </div>

      {/* Step 1 — documents */}
      <form onSubmit={handleParse} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <FileDropzone
            label="Insurance card"
            hint="Drag a photo here — JPG or PNG"
            accept="image/jpeg,image/png"
            extensions={[".jpg", ".jpeg", ".png"]}
            file={cardImage}
            onSelect={setCardImage}
            disabled={parsing}
          />
          <FileDropzone
            label="Evidence of Coverage"
            hint="Drag your EOC here — PDF"
            accept="application/pdf"
            extensions={[".pdf"]}
            file={eocPdf}
            onSelect={setEocPdf}
            disabled={parsing}
          />
        </div>

        <div className="flex flex-wrap items-end gap-4">
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-700">
              Member ID <span className="text-slate-400">(hashed, optional)</span>
            </span>
            <input
              value={memberId}
              onChange={(event) => setMemberId(event.target.value)}
              placeholder="mbr-12345"
              disabled={parsing}
              className="rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-electric-500 focus:outline-none"
            />
          </label>

          <button
            type="submit"
            disabled={!canUpload}
            className="pavo-btn"
          >
            {parsing ? "Reading your documents…" : "Parse documents"}
          </button>
        </div>
      </form>

      {parseError ? (
        <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {parseError}
        </p>
      ) : null}

      {/* Step 2 — the plan and the procedure query */}
      {document ? (
        <>
          <PlanSummary plan={document.insurance_plan} sources={document.sources} />

          <form
            onSubmit={handleQuery}
            className="pavo-card p-5"
          >
            <label htmlFor="procedure" className="block text-sm font-semibold">
              What procedure do you need?
            </label>
            <div className="mt-3 flex flex-wrap gap-2">
              <input
                id="procedure"
                value={procedure}
                onChange={(event) => setProcedure(event.target.value)}
                placeholder="I need an MRI of my knee"
                required
                disabled={querying}
                className="min-w-64 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-electric-500 focus:outline-none"
              />
              <button
                type="submit"
                disabled={querying || !procedure.trim()}
                className="pavo-btn"
              >
                {querying ? "Calling facilities…" : "Find prices"}
              </button>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="text-xs text-navy-400">Try:</span>
              {EXAMPLE_PROCEDURES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setProcedure(example)}
                  className="rounded-full border border-slate-300 px-2.5 py-1 text-xs text-slate-700 hover:border-electric-500"
                >
                  {example}
                </button>
              ))}
            </div>
          </form>
        </>
      ) : null}

      {queryError ? (
        <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {queryError}
        </p>
      ) : null}

      {/* Step 3 — ranked results */}
      {priceQuery ? (
        <section>
          <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-navy-400">
              {priceQuery.results.length} facilities for {priceQuery.procedure_name}
            </h2>
            <p className="text-xs text-navy-400">
              CPT <span className="font-mono">{priceQuery.cpt_code}</span> ·
              deductible {priceQuery.deductible_met ? "met" : "not met"}
            </p>
          </div>

          <ul className="space-y-3">
            {priceQuery.results.map((facility) => (
              <FacilityCard key={facility.facility_id} facility={facility} />
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
