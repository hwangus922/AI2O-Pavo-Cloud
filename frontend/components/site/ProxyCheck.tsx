"use client";

import { useEffect, useState } from "react";

type Result =
  | { kind: "checking" }
  | { kind: "ok"; rules: number }
  | { kind: "fail"; detail: string };

/**
 * Prove the proxy works from the browser, not just from the server.
 *
 * The server can reach the backend directly while the browser's /api/* calls
 * still 404, because those two paths are different: the server uses an
 * absolute BACKEND_ORIGIN, the browser relies on the rewrite. Every page in
 * the app except this one uses the browser path, so it is the one worth
 * testing here — and /api/rules is a cheap, side-effect-free endpoint.
 */
export function ProxyCheck() {
  const [result, setResult] = useState<Result>({ kind: "checking" });

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const response = await fetch("/api/rules", { cache: "no-store" });
        if (!response.ok) {
          if (cancelled) return;
          setResult({
            kind: "fail",
            detail:
              response.status === 404
                ? "404 — nothing is serving /api on this origin, which is what a deployment built without BACKEND_ORIGIN looks like."
                : `The backend answered ${response.status}.`,
          });
          return;
        }
        const rules = (await response.json()) as unknown[];
        if (cancelled) return;
        setResult({ kind: "ok", rules: Array.isArray(rules) ? rules.length : 0 });
      } catch (caught) {
        if (cancelled) return;
        setResult({
          kind: "fail",
          detail: caught instanceof Error ? caught.message : String(caught),
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="mt-10">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-navy-400">
        Browser check
      </h2>
      <div className="pavo-card mt-4 p-5">
        {result.kind === "checking" ? (
          <p className="text-sm text-navy-600">Calling /api/rules…</p>
        ) : result.kind === "ok" ? (
          <>
            <p className="text-sm font-medium text-emerald-800">
              The proxy works — /api/rules returned {result.rules} coverage
              rules.
            </p>
            <p className="mt-1 text-sm leading-relaxed text-navy-600">
              This is the same path every page in the app uses, so if this
              passes, the app can reach the backend.
            </p>
          </>
        ) : (
          <>
            <p className="text-sm font-medium text-rose-800">
              The proxy is not working from the browser.
            </p>
            <p className="mt-1 max-w-2xl text-sm leading-relaxed text-navy-600">
              {result.detail}
            </p>
          </>
        )}
      </div>
    </section>
  );
}
