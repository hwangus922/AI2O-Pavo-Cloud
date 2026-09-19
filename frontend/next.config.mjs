/**
 * @type {import('next').NextConfig}
 *
 * BACKEND_ORIGIN turns this app into a reverse proxy for the API: every
 * /api/* request is forwarded server-side to the FastAPI service. That is how
 * the hosted demo runs, and it removes three things that break hosted demos —
 * a CORS allow-list that has to know the frontend's domain, a browser blocking
 * an https page calling an http API, and the backend's URL being guessable
 * from the client bundle.
 *
 * Unset (local development), nothing is rewritten and the client calls the
 * backend directly via NEXT_PUBLIC_API_BASE_URL, as it always has.
 */
const backendOrigin = process.env.BACKEND_ORIGIN?.replace(/\/+$/, "");

// A Vercel build without BACKEND_ORIGIN used to succeed and ship an app whose
// every data call 404s, with nothing anywhere saying why. Fail the build
// instead. Local builds are exempt: development talks to the backend directly.
if (process.env.VERCEL && !backendOrigin) {
  throw new Error(
    "BACKEND_ORIGIN is not set for this deployment.\n\n" +
      "Without it the /api/* rewrite is not generated, so the site builds " +
      "successfully and then fails on every request for data.\n\n" +
      "Set BACKEND_ORIGIN (the FastAPI service URL, no trailing slash) for " +
      "this environment in the Vercel project settings and redeploy."
  );
}

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    if (!backendOrigin) return [];
    return [{ source: "/api/:path*", destination: `${backendOrigin}/api/:path*` }];
  },
};

export default nextConfig;
