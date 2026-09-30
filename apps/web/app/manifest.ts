import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "ADM",
    short_name: "ADM",
    description: "Единый маршрут ребёнка между медициной, образованием и соцзащитой",
    start_url: "/?source=pwa",
    scope: "/",
    display: "standalone",
    orientation: "any",
    lang: "ru",
    background_color: "#0b0d10",
    theme_color: "#0b0d10",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icons/icon-512-maskable.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
      { src: "/icons/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
    shortcuts: [
      { name: "Мой план", url: "/ru/plan" },
      { name: "Документы", url: "/ru/documents" },
    ],
  };
}
