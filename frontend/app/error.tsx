"use client";

import Link from "next/link";

import { Container } from "@/components/site/Container";

/**
 * The last line of defence.
 *
 * Every data call in the app already swallows its own failures, so nothing
 * routine reaches here. Without this boundary, anything that did would get
 * Next's production fallback — "Application error: a client-side exception
 * has occurred" — which is the worst sentence that could appear on this site.
 */
export default function AppError({ reset }: { reset: () => void }) {
  return (
    <Container className="py-16 sm:py-24">
      <p className="text-sm font-medium uppercase tracking-wide text-electric-600">
        Pavo Cloud
      </p>
      <h1 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl">
        Let&rsquo;s try that again.
      </h1>
      <p className="mt-4 max-w-xl text-base leading-relaxed text-navy-600">
        This view did not finish loading.
      </p>

      <div className="flex flex-wrap gap-3 pt-8">
        <button type="button" onClick={reset} className="pavo-btn">
          Reload this view
        </button>
        <Link href="/" className="pavo-btn-quiet">
          Go to the home page
        </Link>
      </div>
    </Container>
  );
}
