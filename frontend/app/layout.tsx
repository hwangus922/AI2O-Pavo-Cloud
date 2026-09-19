import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";

import { DeploymentBanner } from "@/components/site/DeploymentBanner";
import { Footer } from "@/components/site/Footer";
import { Nav } from "@/components/site/Nav";

import "./globals.css";

// Absolute URLs are needed for og:image. The deployed origin wins; the
// localhost fallback keeps `next build` from warning during development.
const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Pavo Cloud — prior authorization that resolves in minutes",
    template: "%s",
  },
  description:
    "Autonomous prior authorization over the ARIA protocol. Provider and payer agents settle clear cases in seconds, criteria are proven without disclosing the record, and every decision traces to a rule.",
  openGraph: {
    type: "website",
    siteName: "Pavo Cloud",
    title: "Pavo Cloud — prior authorization that resolves in minutes",
    description:
      "Signed agent-to-agent authorization, zero-knowledge proofs over patient criteria, and a deterministic rule behind every decision.",
    images: ["/og.png"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Pavo Cloud — prior authorization that resolves in minutes",
    description:
      "Signed agent-to-agent authorization, zero-knowledge proofs over patient criteria, and a deterministic rule behind every decision.",
    images: ["/og.png"],
  },
};

const clerkConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <DeploymentBanner />
        <Nav />
        {/* Width is deliberately NOT set here. Constraining every page from the
          layout meant no page could draw a band edge to edge, which the
          landing page needs. Each page wraps its own content in <Container>. */}
        <main className="min-h-[60vh]">{children}</main>
        <Footer />
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
