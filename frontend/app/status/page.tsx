import type { Metadata } from "next";

import { Container } from "@/components/site/Container";
import { ProxyCheck } from "@/components/site/ProxyCheck";
import { getBackendOrigin, getDeploymentInfo } from "@/lib/deployment";

export const metadata: Metadata = {
  title: "Status — Pavo Cloud",
  description:
    "Which deployment this is, and whether its API proxy and backend are working.",
};

// Every value on this page is about the request being served right now.
export const dynamic = "force-dynamic";

type Row = {
  label: string;
  value: string;
  state: "ok" | "warn" | "bad" | "info";
  note?: string;
};

const STATE_STYLES: Record<Row["state"], string> = {
  ok: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  warn: "bg-amber-50 text-amber-800 ring-amber-200",
  bad: "bg-rose-50 text-rose-800 ring-rose-200",
  info: "bg-slate-100 text-navy-600 ring-slate-200",
};

/** Ask the backend directly, server-side, bypassing the rewrite. */
async function probeBackend(origin: string): Promise<
  | { ok: true; body: Record<string, unknown> }
  | { ok: false; detail: string }
> {
  try {
    const response = await fetch(`${origin}/health`, {
      cache: "no-store",
      // A sleeping free-tier instance can take ~50s; don't hang forever.
      signal: AbortSignal.timeout(20000),
    });
    if (!response.ok) {
      return { ok: false, detail: `responded ${response.status}` };
    }
    return { ok: true, body: (await response.json()) as Record<string, unknown> };
  } catch (caught) {
    const message = caught instanceof Error ? caught.message : String(caught);
    return {
      ok: false,
      detail: /timeout|abort/i.test(message)
        ? "timed out after 20s — a sleeping instance can take ~50s to wake"
        : message,
    };
  }
}

export default async function StatusPage() {
  const deployment = getDeploymentInfo();
  const backendOrigin = getBackendOrigin();
  const probe = backendOrigin ? await probeBackend(backendOrigin) : null;

  const rows: Row[] = [
    {
      label: "Environment",
      value: deployment.isLocal ? "local development" : deployment.environment!,
      state: deployment.isProduction ? "ok" : deployment.isLocal ? "info" : "warn",
      note: deployment.isProduction
        ? undefined
        : deployment.isLocal
          ? "Running outside Vercel."
          : "This is NOT the live site. A branch preview keeps serving the code it was built from, forever.",
    },
    {
      label: "Branch",
      value: deployment.branch ?? "—",
      state: !deployment.branch
        ? "info"
        : deployment.branch === "main"
          ? "ok"
          : "warn",
      note:
        deployment.branch && deployment.branch !== "main"
          ? "Built from a branch other than main, so it may be missing later fixes."
          : undefined,
    },
    {
      label: "Commit",
      value: deployment.commit ?? "—",
      state: "info",
      note: "The only thing that actually identifies which code you are looking at.",
    },
    {
      label: "API proxy",
      value: backendOrigin ? backendOrigin : "NOT CONFIGURED",
      state: backendOrigin ? "ok" : "bad",
      note: backendOrigin
        ? undefined
        : "BACKEND_ORIGIN was unset when this deployment was built, so /api/* is not forwarded anywhere and every data call will fail. Set it for this environment in Vercel and redeploy.",
    },
  ];

  if (probe) {
    rows.push({
      label: "Backend reachable",
      value: probe.ok ? "yes" : "no",
      state: probe.ok ? "ok" : "bad",
      note: probe.ok ? undefined : probe.detail,
    });
  }

  if (probe?.ok) {
    const body = probe.body;
    const zk = body.zk_artifacts_available === true;
    rows.push(
      {
        label: "ZK artifacts",
        value: zk ? "available" : "missing",
        state: zk ? "ok" : "bad",
        note: zk
          ? undefined
          : "Demo step 3 will fail — the circuit artifacts are not in the image.",
      },
      {
        label: "Storage",
        value: String(body.storage_backend ?? "—"),
        state: "info",
        note: "In-memory is expected; the demo seeds what it needs on each run.",
      },
      {
        label: "Model provider",
        value: String(body.llm_provider ?? "none"),
        state: body.llm_provider ? "info" : "warn",
        note: body.llm_provider
          ? "Appeal letters and CPT mapping reach the model. Document parsing needs a vision-capable provider."
          : "No model configured — appeals escalate instead of drafting. The six demo steps do not use the model and are unaffected.",
      },
    );
  }

  const healthy =
    Boolean(backendOrigin) && probe?.ok === true && deployment.isProduction;

  return (
    <Container className="py-12 sm:py-16">
      <p className="text-sm font-medium uppercase tracking-wide text-electric-600">
        Status
      </p>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
        {healthy
          ? "This deployment is the live site and everything is wired up."
          : "What this deployment is, and what is wired up."}
      </h1>
      <p className="mt-3 max-w-2xl text-base leading-relaxed text-navy-600">
        Checked on every request. If something on the site is failing, the cause
        is almost always one of the rows below.
      </p>

      <dl className="mt-10 divide-y divide-slate-200 border-y border-slate-200">
        {rows.map((row) => (
          <div
            key={row.label}
            className="grid gap-2 py-4 sm:grid-cols-[12rem_1fr] sm:gap-6"
          >
            <dt className="text-sm font-medium text-navy-600">{row.label}</dt>
            <dd className="min-w-0">
              <span
                className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                  STATE_STYLES[row.state]
                }`}
              >
                <span className="break-all font-mono">{row.value}</span>
              </span>
              {row.note ? (
                <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-navy-600">
                  {row.note}
                </p>
              ) : null}
            </dd>
          </div>
        ))}
      </dl>

      <ProxyCheck />
    </Container>
  );
}
