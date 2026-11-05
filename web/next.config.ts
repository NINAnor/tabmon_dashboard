import type { NextConfig } from "next";

// In production Traefik routes /api to the API container directly; this rewrite
// is the fallback for local development and single-container setups.
const apiUrl = process.env.API_URL ?? "http://localhost:8000";

const config: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiUrl}/api/:path*` }];
  },
};

export default config;
