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

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    if (!backendOrigin) return [];
    return [{ source: "/api/:path*", destination: `${backendOrigin}/api/:path*` }];
  },
};

export default nextConfig;
