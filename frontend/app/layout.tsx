import type { Metadata } from "next";
import Link from "next/link";
import { ClerkProvider, SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";

import "./globals.css";

export const metadata: Metadata = {
  title: "Pavo Cloud",
  description:
    "Autonomous prior authorization over the ARIA protocol. Every decision traces to a rule.",
};

const clerkConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Link href="/" className="flex items-center gap-2">
              <span className="inline-block h-6 w-6 rounded bg-slate-900" aria-hidden />
              <span className="text-base font-semibold tracking-tight">Pavo Cloud</span>
            </Link>

            <nav className="flex items-center gap-6 text-sm">
              <Link href="/dashboard" className="text-slate-600 hover:text-slate-900">
                Dashboard
              </Link>
              {clerkConfigured ? (
                <>
                  <SignedOut>
                    <SignInButton mode="modal">
                      <button className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700">
                        Sign in
                      </button>
                    </SignInButton>
                  </SignedOut>
                  <SignedIn>
                    <UserButton afterSignOutUrl="/" />
                  </SignedIn>
                </>
              ) : (
                <span className="rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">
                  Auth not configured
                </span>
              )}
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>

        <footer className="border-t border-slate-200 py-6">
          <div className="mx-auto max-w-6xl px-6 text-xs text-slate-500">
            ARIA Protocol v1.0 — every decision carries the rule that produced it.
          </div>
        </footer>
      </body>
    </html>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // ClerkProvider throws without a publishable key, so it is only mounted once
  // the key is present. The app stays runnable before auth is configured.
  if (!clerkConfigured) {
    return <Shell>{children}</Shell>;
  }

  return (
    <ClerkProvider>
      <Shell>{children}</Shell>
    </ClerkProvider>
  );
}
