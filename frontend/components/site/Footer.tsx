import Link from "next/link";

import { Container } from "./Container";
import { APP_LINKS, PRODUCT_LINKS } from "./nav-links";

const REPO_URL = "https://github.com/hwangus922/AI2O-Pavo-Cloud";

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <Container className="py-10">
        <div className="grid gap-8 sm:grid-cols-3">
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-navy-400">
              Product
            </h2>
            <ul className="mt-3 space-y-2">
              {PRODUCT_LINKS.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-navy-600 transition hover:text-navy-900"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-navy-400">
              The system
            </h2>
            <ul className="mt-3 space-y-2">
              {APP_LINKS.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-navy-600 transition hover:text-navy-900"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-navy-400">
              Project
            </h2>
            <ul className="mt-3 space-y-2">
              <li>
                <a
                  href={REPO_URL}
                  className="text-sm text-navy-600 transition hover:text-navy-900"
                >
                  Source on GitHub
                </a>
              </li>
              <li>
                <span className="text-sm text-navy-600">
                  Built for the AI2O finals
                </span>
              </li>
            </ul>
          </div>
        </div>

        <p className="mt-10 border-t border-slate-200 pt-6 text-xs text-navy-400">
          ARIA Protocol v1.0 — every decision carries the rule that produced it.
        </p>
      </Container>
    </footer>
  );
}
