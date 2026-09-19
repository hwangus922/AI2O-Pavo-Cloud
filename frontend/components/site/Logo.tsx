/**
 * The Pavo mark.
 *
 * Pavo is Latin for peacock, so the mark is a fan of five plumes springing
 * from a single quill, each carrying the eye that a peacock feather carries.
 *
 * Two things drive the geometry. The plumes are slender rather than round —
 * a fat teardrop reads as a water droplet, and one alone reads as a map pin.
 * And the outer pairs sit further back in progressively darker blues, which
 * is what keeps the fan from collapsing into a single silhouette at 24px.
 *
 * The eyes are navy, so the mark is drawn for a navy ground: the header, the
 * favicon tile and the share image. On white it would need a light eye.
 */

/** One plume: quill at (16, 31), widening to a bulb centred at (16, 11.5). */
const PLUME =
  "M16 31C14.4 25 12.4 18 12.4 11.5a3.6 3.6 0 0 1 7.2 0c0 6.5-1.6 13.5-3.6 19.5Z";

const NAVY = "#0A1B33";

/**
 * Drawn back to front, so the centre plume overlaps the pairs behind it.
 * electric-600 → 500 → 400: the pairs recede, and even the darkest still
 * separates from the navy-900 ground it sits on.
 */
const PLUMES = [
  { angle: -47, scale: 0.75, fill: "#0B5CD6" },
  { angle: 47, scale: 0.75, fill: "#0B5CD6" },
  { angle: -25, scale: 0.88, fill: "#2F80FF" },
  { angle: 25, scale: 0.88, fill: "#2F80FF" },
  { angle: 0, scale: 1, fill: "#4D9BFF" },
];

/** Rotate and scale about the quill, so every plume springs from one point. */
function aboutQuill(angle: number, scale: number): string {
  return `translate(16 31) rotate(${angle}) scale(${scale}) translate(-16 -31)`;
}

export function PavoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={className}
      role="img"
      aria-label="Pavo Cloud"
    >
      {/* Pulled in slightly so the widest plumes clear the viewBox edge. */}
      <g transform="translate(16 31) scale(0.87) translate(-16 -31)">
        {PLUMES.map((plume) => (
          <g
            key={`${plume.angle}`}
            transform={aboutQuill(plume.angle, plume.scale)}
          >
            <path d={PLUME} fill={plume.fill} />
            <circle cx="16" cy="11.2" r="1.45" fill={NAVY} />
          </g>
        ))}
      </g>
    </svg>
  );
}

/** Mark plus wordmark, as it appears in the header. */
export function Logo() {
  return (
    <span className="flex items-center gap-2">
      <PavoMark className="h-8 w-8" />
      <span className="text-base font-semibold tracking-tight text-white">
        Pavo Cloud
      </span>
    </span>
  );
}
