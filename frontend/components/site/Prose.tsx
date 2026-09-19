import type { ReactNode } from "react";

/**
 * Body copy for the explanatory pages.
 *
 * Tailwind's typography plugin is not installed and adding it for four pages
 * is not worth a dependency, so the measure and rhythm live here instead.
 */
export function Prose({
  className = "",
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={`max-w-2xl space-y-4 text-sm leading-relaxed text-navy-600 ${className}`.trim()}
    >
      {children}
    </div>
  );
}
