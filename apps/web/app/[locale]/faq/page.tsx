"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { AppChrome } from "@/components/AppChrome";

type Item = { q: string; a: string };

export default function FaqPage() {
  const t = useTranslations("faq");
  const router = useRouter();
  const items = t.raw("items") as Item[];

  return (
    <main className="min-h-dvh">
      <AppChrome hideInstall />
      <div className="max-w-2xl mx-auto w-full px-4 sm:px-6 py-6">
        <button onClick={() => router.back()} className="tap-target inline-flex items-center gap-1 text-sm text-muted mb-4">
          ← {t("back")}
        </button>
        <h1 className="text-2xl font-semibold mb-1">{t("title")}</h1>
        <p className="text-muted mb-6">{t("subtitle")}</p>
        <div className="flex flex-col gap-2">
          {items.map((item, i) => (
            <details key={i} className="group rounded-xl border border-border bg-card open:border-medicine/50">
              <summary className="tap-target flex items-center justify-between gap-3 cursor-pointer list-none px-4 py-3 font-medium">
                {item.q}
                <svg viewBox="0 0 24 24" className="w-5 h-5 shrink-0 text-muted group-open:rotate-180" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </summary>
              <p className="px-4 pb-4 text-muted leading-relaxed">{item.a}</p>
            </details>
          ))}
        </div>
      </div>
    </main>
  );
}
