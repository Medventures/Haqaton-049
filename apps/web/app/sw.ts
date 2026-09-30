/// <reference lib="webworker" />
import { defaultCache } from "@serwist/next/worker";
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";
import { NetworkFirst, NetworkOnly, Serwist, ExpirationPlugin } from "serwist";

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined;
  }
}

declare const self: ServiceWorkerGlobalScope;

// Раздел 16.2 SPEC.md.
const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  precacheOptions: { cleanupOutdatedCaches: true },
  skipWaiting: false,
  clientsClaim: true,
  navigationPreload: true,
  fallbacks: { entries: [{ url: "/offline", matcher: ({ request }) => request.mode === "navigate" }] },
  runtimeCaching: [
    {
      matcher: ({ url, sameOrigin }) =>
        sameOrigin && (url.pathname.startsWith("/api/plans/") || url.pathname === "/api/documents" || url.pathname === "/api/notifications"),
      handler: new NetworkFirst({
        cacheName: "api-private",
        plugins: [new ExpirationPlugin({ maxAgeSeconds: 7 * 24 * 60 * 60 })],
      }),
    },
    {
      // PDF и файлы документов: NetworkOnly, API отдаёт их с Cache-Control: no-store.
      matcher: ({ url, sameOrigin }) => sameOrigin && (url.pathname.startsWith("/api/reports/") || url.pathname.startsWith("/api/documents/")),
      handler: new NetworkOnly(),
    },
    {
      // Остальные GET /api/*, а также все POST/PATCH/DELETE — NetworkOnly.
      matcher: ({ url, sameOrigin }) => sameOrigin && url.pathname.startsWith("/api/"),
      handler: new NetworkOnly(),
    },
    ...defaultCache,
  ],
});

serwist.addEventListeners();

self.addEventListener("message", (event) => {
  if (event.data === "LOGOUT_CLEAR_PRIVATE_CACHE") {
    event.waitUntil(caches.delete("api-private"));
  }
  if (event.data?.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});
