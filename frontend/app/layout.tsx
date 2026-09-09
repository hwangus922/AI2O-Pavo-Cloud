import type { Metadata } from "next";
import Link from "next/link";
import {
  ClerkProvider,
  SignedIn,
  SignedOut,
  SignInButton,
  UserButton,
} from "@clerk/nextjs";

import "./globals.css";

export const metadata: Metadata = {
  title: "Pavo Cloud",
  description:
    "Autonomous prior authorization over the ARIA protocol. Every decision traces to a rule.",
};

const clerkConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

const NAV_LINKS = [
  { href: "/demo", label: "Demo" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/insure", label: "Insure" },
  { href: "/audit", label: "Audit" },
];

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <header className="border-b border-navy-800 bg-navy-900">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 sm:py-4">
            <Link href="/" className="flex items-center gap-2">
              <span
                className="inline-block h-6 w-6 rounded bg-electric-500"
                aria-hidden
              />
              <span className="text-base font-semibold tracking-tight text-white">
                Pavo Cloud
              </span>
            </Link>

            <nav className="flex flex-wrap items-center gap-4 text-sm sm:gap-6">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-navy-200 transition hover:text-white"
                >
                  {link.label}
                </Link>
              ))}

              {clerkConfigured ? (
                <>
                  <SignedOut>
                    <SignInButton mode="modal">
                      <button className="rounded-md bg-electric-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-electric-500">
                        Sign in
                      </button>
                    </SignInButton>
                  </SignedOut>
                  <SignedIn>
                    <UserButton afterSignOutUrl="/" />
                  </SignedIn>
                </>
              ) : (
                <span className="rounded-md bg-navy-800 px-2 py-1 text-xs font-medium text-navy-200">
                  Auth not configured
                </span>
              )}
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
          {children}
        </main>

        <footer className="border-t border-slate-200 py-6">
          <div className="mx-auto max-w-6xl px-4 text-xs text-navy-400 sm:px-6">
            ARIA Protocol v1.0 — every decision carries the rule that produced it.
          </div>
        </footer>
      </body>
    </html>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // ClerkProvider throws without a publishable key, so it is only mounted
  // once the key is present. The app stays runnable before auth is set up.
  if (!clerkConfigured) {
    return <Shell>{children}</Shell>;
  }

  return (
    <ClerkProvider>
      <Shell>{children}</Shell>
    </ClerkProvider>
  );
}
