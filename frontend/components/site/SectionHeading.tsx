import type { ReactNode } from "react";

/**
 * Eyebrow + heading + lede, in the type scale the app already uses.
 *
 * `invert` flips the three colours for a dark section rather than taking a
 * free-form className, so a heading cannot end up unreadable on navy.
 */
export function SectionHeading({
  eyebrow,
  title,
  lede,
  invert = false,
}: {
  eyebrow?: string;
  title: ReactNode;
  lede?: ReactNode;
  invert?: boolean;
}) {
  return (
    <div className="max-w-3xl">
      {eyebrow ? (
        <p
          className={`text-sm font-medium uppercase tracking-wide ${
            invert ? "text-electric-400" : "text-electric-600"
          }`}
        >
          {eyebrow}
        </p>
      ) : null}
      <h2
        className={`mt-2 text-2xl font-semibold tracking-tight sm:text-3xl ${
          invert ? "text-white" : ""
        }`.trim()}
      >
        {title}
      </h2>
      {lede ? (
        <p
          className={`mt-3 max-w-2xl text-base leading-relaxed ${
            invert ? "text-navy-200" : "text-navy-600"
          }`}
        >
          {lede}
        </p>
      ) : null}
    </div>
  );
}
