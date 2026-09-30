import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";
import withSerwistInit from "@serwist/next";

const withNextIntl = createNextIntlPlugin();
const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",
  swDest: "public/sw.js",
});

const API_URL = process.env.API_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    // Раздел 13 SPEC.md: /api/* на API_URL через rewrite, чтобы cookie и
    // service worker работали на одном домене. На Vercel /api/* уходит в
    // сервис api через rewrites в корневом vercel.json, до Next.js.
    if (process.env.VERCEL) return [];
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default withSerwist(withNextIntl(nextConfig));
