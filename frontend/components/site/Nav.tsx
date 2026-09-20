import Link from "next/link";
import {
  SignedIn,
  SignedOut,
  SignInButton,
  UserButton,
} from "@clerk/nextjs";

import { Container } from "./Container";
import { Logo } from "./Logo";
import { APP_LINKS, PRODUCT_LINKS } from "./nav-links";

const clerkConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

/**
 * Sign-in, when there is auth to sign into.
 *
 * Without a Clerk key there is nothing to render here — the header simply
 * ends at the last nav link. ClerkProvider is only mounted when the key is
 * present, so these components must not render without one.
 */
function AuthSlot() {
  if (!clerkConfigured) return null;

  return (
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
  );
}

const linkClass = "text-navy-200 transition hover:text-white";

export function Nav() {
  return (
    <header className="border-b border-navy-800 bg-navy-900">
      {/* Mobile: a native disclosure, so the menu needs no JavaScript and works
        before hydration. The panel stays in normal flow and pushes the page
        down — a closed <details> is a containing block in Chrome, so an
        absolutely positioned panel would collapse to the button's width and
        overflow the viewport. */}
      <details className="md:hidden">
        <summary className="cursor-pointer list-none [&::-webkit-details-marker]:hidden">
          <Container className="flex items-center justify-between gap-3 py-3">
            <Logo />
            <span className="rounded-md border border-navy-700 px-3 py-1.5 text-sm text-navy-200">
              Menu
            </span>
          </Container>
        </summary>
        <Container className="pb-4">
          <nav>
            <ul className="space-y-3 border-t border-navy-800 pt-4">
              <li>
                <Link href="/" className={`block ${linkClass}`}>
                  Home
                </Link>
              </li>
              {PRODUCT_LINKS.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className={`block ${linkClass}`}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
            <ul className="mt-4 space-y-3 border-t border-navy-800 pt-4">
              {APP_LINKS.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className={`block ${linkClass}`}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
            <div className="mt-4">
              <AuthSlot />
            </div>
          </nav>
        </Container>
      </details>

      {/* Desktop: two groups, divided, so "what the product is" reads
        separately from "the running system". */}
      <div className="hidden md:block">
        <Container className="flex items-center justify-between gap-3 py-4">
          <Link href="/">
            <Logo />
          </Link>
          <nav className="flex items-center gap-6 text-sm">
            {PRODUCT_LINKS.map((link) => (
              <Link key={link.href} href={link.href} className={linkClass}>
                {link.label}
              </Link>
            ))}
            <span aria-hidden className="h-4 w-px bg-navy-700" />
            {APP_LINKS.map((link) => (
              <Link key={link.href} href={link.href} className={linkClass}>
                {link.label}
              </Link>
            ))}
            <AuthSlot />
          </nav>
        </Container>
      </div>
    </header>
  );
}
