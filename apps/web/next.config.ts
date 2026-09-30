import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";
import withSerwistInit from "@serwist/next";

const withNextIntl = createNextIntlPlugin();
const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",
  swDest: "public/sw.js",
});

// На Vercel API живёт на отдельном хостинге (раздел 2 SPEC.md). Без
// API_URL сайт собирается, но /api/* не проксируется — только предупреждаем,
// чтобы превью веток не падали.
const API_URL = process.env.API_URL || (process.env.VERCEL ? "" : "http://localhost:8000");
if (!API_URL) {
  console.warn("API_URL is not set: /api/* will not be proxied. Set it in Vercel env to the API's public URL.");
}

const nextConfig: NextConfig = {
  async rewrites() {
    // Раздел 13 SPEC.md: /api/* на API_URL через rewrite, чтобы cookie и
    // service worker работали на одном домене.
    if (!API_URL) return [];
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default withSerwist(withNextIntl(nextConfig));
