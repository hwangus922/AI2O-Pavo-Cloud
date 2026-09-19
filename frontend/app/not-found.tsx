import Link from "next/link";

import { Container } from "@/components/site/Container";

/**
 * What an unknown URL renders.
 *
 * Next's built-in page is a bare "404 — this page could not be found", which
 * is the one screen on the whole site a visitor is most likely to read as
 * "the thing is broken". This one offers the way onward instead.
 */
export default function NotFound() {
  return (
    <Container className="py-16 sm:py-24">
      <p className="text-sm font-medium uppercase tracking-wide text-electric-600">
        Pavo Cloud
      </p>
      <h1 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl">
        There is nothing at this address.
      </h1>
      <p className="mt-4 max-w-xl text-base leading-relaxed text-navy-600">
        Every page is one click away, in the header above or the footer below.
      </p>

      <div className="flex flex-wrap gap-3 pt-8">
        <Link href="/" className="pavo-btn">
          Go to the home page
        </Link>
        <Link href="/demo" className="pavo-btn-quiet">
          Run the demo
        </Link>
      </div>
    </Container>
  );
}
