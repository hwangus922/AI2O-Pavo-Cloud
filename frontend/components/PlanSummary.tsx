import { formatCurrency, toNumber } from "@/lib/format";
import type { InsurancePlan, ParserSources } from "@/lib/types";

function Field({
  label,
  value,
}: {
  label: string;
  value: string | number | null;
}) {
  return (
    <div>
      <dt className="text-xs text-navy-400">{label}</dt>
      <dd className="mt-0.5 text-sm font-medium">{value ?? "—"}</dd>
    </div>
  );
}

export function PlanSummary({
  plan,
  sources,
}: {
  plan: InsurancePlan;
  sources: ParserSources;
}) {
  const usedSamples = sources.card === "sample" || sources.eoc === "sample";
  const deductible = toNumber(plan.deductible_individual);
  const met = toNumber(plan.deductible_met);
  const remaining =
    deductible !== null && met !== null ? Math.max(deductible - met, 0) : null;

  return (
    <section className="pavo-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">Your plan</h2>
        {usedSamples ? (
          <span className="rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">
            Sample data — set ANTHROPIC_API_KEY to parse real documents
          </span>
        ) : (
          <span className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-800">
            Parsed from your documents
          </span>
        )}
      </div>

      <dl className="mt-4 grid gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <Field label="Plan" value={plan.plan_name} />
        <Field label="Insurer" value={plan.insurance_company} />
        <Field label="Network" value={plan.network_name} />
        <Field label="Group" value={plan.group_number} />
        <Field
          label="Deductible (individual)"
          value={formatCurrency(plan.deductible_individual)}
        />
        <Field label="Deductible met" value={formatCurrency(plan.deductible_met)} />
        <Field
          label="Remaining"
          value={remaining === null ? "—" : formatCurrency(remaining)}
        />
        <Field
          label="Coinsurance"
          value={
            plan.coinsurance_percentage === null
              ? "—"
              : `${toNumber(plan.coinsurance_percentage)}%`
          }
        />
        <Field
          label="Out-of-pocket max"
          value={formatCurrency(plan.out_of_pocket_max_individual)}
        />
        <Field label="Specialist copay" value={formatCurrency(plan.specialist_copay)} />
        <Field label="Primary care copay" value={formatCurrency(plan.primary_care_copay)} />
        <Field label="ER copay" value={formatCurrency(plan.er_copay)} />
      </dl>

      {plan.prior_auth_required_for?.length ? (
        <div className="mt-4 border-t border-slate-100 pt-4">
          <p className="text-xs text-navy-400">Prior authorization required for</p>
          <ul className="mt-1 flex flex-wrap gap-1.5">
            {plan.prior_auth_required_for.map((service) => (
              <li
                key={service}
                className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700"
              >
                {service}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
