import type { ReactNode } from "react";

import { Container } from "./Container";

type Tone = "default" | "panel" | "dark";

// `default` sits on the page's slate-50; `panel` lifts a band to white so
// adjacent sections separate without a divider; `dark` is the navy ground the
// brand is built on, used sparingly for the sections that carry the most weight.
const TONE_CLASS: Record<Tone, string> = {
  default: "",
  panel: "border-y border-slate-200 bg-white",
  dark: "bg-navy-900 text-white",
};

export function Section({
  id,
  tone = "default",
  className = "",
  children,
}: {
  id?: string;
  tone?: Tone;
  className?: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className={`py-14 sm:py-20 ${TONE_CLASS[tone]}`.trim()}>
      <Container className={className}>{children}</Container>
    </section>
  );
}
