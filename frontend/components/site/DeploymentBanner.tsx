import { getDeploymentInfo } from "@/lib/deployment";

/**
 * Say so, loudly, when this is not the live site.
 *
 * Vercel keeps every branch preview serving the code it was built from, and
 * those URLs are easy to keep open and hard to tell apart — which is exactly
 * how an already-fixed bug gets reported again. Production renders nothing.
 */
export function DeploymentBanner() {
  const { isProduction, isLocal, branch, commit } = getDeploymentInfo();

  if (isProduction || isLocal) return null;

  return (
    <div className="bg-amber-100 text-amber-900">
      <div className="mx-auto max-w-6xl px-4 py-2 text-xs sm:px-6">
        <span className="font-semibold">Preview deployment — not the live site.</span>{" "}
        Built from{" "}
        <span className="font-mono">{branch ?? "an unknown branch"}</span>
        {commit ? (
          <>
            {" at "}
            <span className="font-mono">{commit}</span>
          </>
        ) : null}
        . It will keep serving this code even after the branch is merged.{" "}
        <a href="/status" className="underline">
          Status
        </a>
      </div>
    </div>
  );
}
