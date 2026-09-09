"use client";

import { useState } from "react";

import { formatCurrency, formatCurrencyPrecise } from "@/lib/format";
import type { RankedFacility } from "@/lib/types";

function QualityStars({ score }: { score: number }) {
  return (
    <span
      className="text-sm tracking-tight text-amber-500"
      aria-label={`Quality score ${score} out of 5`}
      title={`Quality score ${score} of 5`}
    >
      {"★".repeat(score)}
      <span className="text-slate-300">{"★".repeat(5 - score)}</span>
    </span>
  );
}

export function FacilityCard({ facility }: { facility: RankedFacility }) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const { breakdown } = facility;
  const cashIsCheaper = facility.cheaper_option === "cash";

  return (
    <li className="pavo-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-400">
              #{facility.rank}
            </span>
            <h3 className="truncate text-base font-semibold">{facility.name}</h3>
          </div>
          <p className="mt-0.5 text-xs text-navy-400">
            {facility.type} · {facility.city} · {facility.distance_miles} mi
          </p>
          <div className="mt-2 flex items-center gap-2">
            <QualityStars score={facility.quality_score} />
            <span className="text-xs text-navy-400">
              {facility.quality_score}/5
            </span>
          </div>
        </div>

        <div className="text-right">
          <p className="text-xs text-navy-400">You pay</p>
          <p className="text-3xl font-semibold tracking-tight">
            {formatCurrency(facility.you_pay)}
          </p>
          <span
            className={`mt-1 inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
              cashIsCheaper
                ? "bg-emerald-50 text-emerald-800 ring-emerald-200"
                : "bg-sky-50 text-sky-800 ring-sky-200"
            }`}
          >
            {cashIsCheaper ? "Cash is cheaper" : "Insurance is cheaper"}
          </span>
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-4 border-t border-slate-100 pt-4 sm:grid-cols-4">
        <div>
          <dt className="text-xs text-navy-400">Negotiated rate</dt>
          <dd className="mt-0.5 text-sm">{formatCurrency(facility.negotiated_rate)}</dd>
        </div>
        <div>
          <dt className="text-xs text-navy-400">Cash price</dt>
          <dd className="mt-0.5 text-sm">{formatCurrency(facility.cash_price)}</dd>
        </div>
        <div>
          <dt className="text-xs text-navy-400">Cash discount</dt>
          <dd className="mt-0.5 text-sm">{facility.cash_discount_percentage}%</dd>
        </div>
        <div>
          <dt className="text-xs text-navy-400">
            {cashIsCheaper ? "Saved vs insurance" : "Saved vs cash"}
          </dt>
          <dd className="mt-0.5 text-sm">
            {formatCurrency(facility.savings_vs_alternative)}
          </dd>
        </div>
      </dl>

      <div className="mt-4">
        <button
          type="button"
          onClick={() => setShowBreakdown((open) => !open)}
          aria-expanded={showBreakdown}
          className="text-xs font-medium text-slate-700 underline underline-offset-2 hover:text-slate-900"
        >
          {showBreakdown ? "Hide" : "Show"} cost breakdown
        </button>

        {showBreakdown ? (
          <div className="mt-3 rounded-md bg-slate-50 p-4 text-xs">
            <p className="text-navy-600">
              Deductible{" "}
              <span className="font-medium">
                {breakdown.deductible_met ? "met" : "not met"}
              </span>
              , so the rule applied is{" "}
              <span className="font-mono font-medium">{breakdown.rule}</span>.
            </p>

            <dl className="mt-3 space-y-2">
              <div className="flex justify-between gap-4">
                <dt className="text-navy-400">Formula</dt>
                <dd className="font-mono">{breakdown.formula}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-navy-400">Coinsurance</dt>
                <dd>{Math.round(breakdown.coinsurance_rate * 100)}%</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-navy-400">Negotiated rate</dt>
                <dd>{formatCurrencyPrecise(breakdown.negotiated_rate)}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-navy-400">Cost through insurance</dt>
                <dd>{formatCurrencyPrecise(breakdown.insurance_cost)}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-navy-400">Cost paying cash</dt>
                <dd>{formatCurrencyPrecise(breakdown.cash_cost)}</dd>
              </div>
            </dl>

            <p className="mt-3 border-t border-slate-200 pt-3 font-mono text-slate-800">
              {breakdown.calculation}
            </p>
          </div>
        ) : null}
      </div>
    </li>
  );
}
