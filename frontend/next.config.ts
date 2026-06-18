import path from "path";
import type { NextConfig } from "next";

// Proxy /api/* to the FastAPI backend so the browser talks same-origin
// (no CORS), and the backend URL lives in one place.
const nextConfig: NextConfig = {
  // Pin the tracing root to this app so the root package-lock.json (used by
  // the combined `npm run dev` orchestrator) doesn't trigger a workspace warning.
  outputFileTracingRoot: path.resolve(__dirname),
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
