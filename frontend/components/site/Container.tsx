import type { ReactNode } from "react";

/**
 * The page-width wrapper.
 *
 * This measure used to live on `<main>` in the root layout, which meant no page
 * could ever draw a band edge to edge. The layout now leaves width alone and
 * each page wraps its own content instead, so the marketing pages can run
 * full-bleed sections while the app pages keep exactly the measure they had.
 */
export function Container({
  className = "",
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div className={`mx-auto max-w-6xl px-4 sm:px-6 ${className}`.trim()}>
      {children}
    </div>
  );
}
