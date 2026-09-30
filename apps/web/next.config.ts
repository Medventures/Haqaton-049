import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin();

const API_URL = process.env.API_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    // Раздел 13 SPEC.md: /api/* на API_URL через rewrite, чтобы cookie и
    // service worker работали на одном домене.
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default withNextIntl(nextConfig);
