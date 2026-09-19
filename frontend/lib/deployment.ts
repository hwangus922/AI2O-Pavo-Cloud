/**
 * Which deployment is this?
 *
 * Vercel builds a URL per branch, and those previews keep serving their old
 * code forever. Opening one and concluding the app is broken is an easy and
 * expensive mistake, so every value needed to tell deployments apart is read
 * here, once, and surfaced in the UI.
 *
 * These are Vercel system environment variables. Locally they are all absent,
 * which is itself the answer: this is a development build.
 */
export type DeploymentInfo = {
  /** "production" | "preview" | "development", or null when not on Vercel. */
  environment: string | null;
  /** The git branch this deployment was built from. */
  branch: string | null;
  /** Short commit SHA, which is what actually identifies the code. */
  commit: string | null;
  /** True only for the live site. */
  isProduction: boolean;
  /** True when running outside Vercel entirely. */
  isLocal: boolean;
};

export function getDeploymentInfo(): DeploymentInfo {
  const environment = process.env.VERCEL_ENV ?? null;
  const branch = process.env.VERCEL_GIT_COMMIT_REF ?? null;
  const sha = process.env.VERCEL_GIT_COMMIT_SHA ?? null;

  return {
    environment,
    branch,
    commit: sha ? sha.slice(0, 7) : null,
    isProduction: environment === "production",
    isLocal: environment === null,
  };
}

/** The origin the /api rewrite forwards to, or null when unconfigured. */
export function getBackendOrigin(): string | null {
  const origin = process.env.BACKEND_ORIGIN?.replace(/\/+$/, "");
  return origin || null;
}
