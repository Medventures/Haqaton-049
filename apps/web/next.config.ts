import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";
import withSerwistInit from "@serwist/next";

const withNextIntl = createNextIntlPlugin();
const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",
  swDest: "public/sw.js",
});

// На Vercel API живёт на отдельном Docker-хостинге (раздел 2 SPEC.md), без
// API_URL rewrite ушёл бы на localhost — лучше упасть на сборке.
if (process.env.VERCEL && !process.env.API_URL) {
  throw new Error("API_URL must be set on Vercel (public HTTPS URL of the API)");
}
const API_URL = process.env.API_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    // Раздел 13 SPEC.md: /api/* на API_URL через rewrite, чтобы cookie и
    // service worker работали на одном домене.
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default withSerwist(withNextIntl(nextConfig));
