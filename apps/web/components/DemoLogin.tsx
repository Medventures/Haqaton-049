"use client";

import { useEffect, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type Account = { key: string; role: "parent" | "curator"; name: string; email: string };

/**
 * Быстрый вход в демо-аккаунты (раздел 19.5) одной кнопкой. Виден только при
 * DEMO_MODE: иначе /demo/accounts отвечает 403 и блок не рисуется.
 */
export function DemoLogin({ role }: { role?: string | null }) {
  const t = useTranslations("demo");
  const locale = useLocale();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    api.get<Account[]>("/demo/accounts").then(setAccounts).catch(() => setAccounts([]));
  }, []);

  if (!accounts.length) return null;

  const sorted = role ? [...accounts].sort((a, b) => Number(b.role === role) - Number(a.role === role)) : accounts;

  async function enter(account: Account) {
    setBusy(account.key);
    try {
      await api.post("/demo/login", { key: account.key });
      router.push(account.role === "curator" ? `/${locale}/curator` : `/${locale}/plan`);
    } catch {
      setBusy(null);
    }
  }

  return (
    <section className="w-full max-w-sm">
      <div className="flex items-center gap-3 my-2 text-xs text-muted">
        <span className="h-px flex-1 bg-border" />
        {t("title")}
        <span className="h-px flex-1 bg-border" />
      </div>
      <div className="flex flex-col gap-2">
        {sorted.map((a) => (
          <button
            key={a.key}
            onClick={() => enter(a)}
            disabled={busy !== null}
            className={`tap-target flex items-center gap-3 rounded-xl border bg-card px-4 py-3 text-left hover:border-medicine/60 disabled:opacity-60 ${
              role && a.role === role ? "border-medicine/60" : "border-border"
            }`}
          >
            <span
              aria-hidden
              className={`flex items-center justify-center w-10 h-10 rounded-full text-sm font-semibold shrink-0 ${
                a.role === "curator" ? "bg-education/15 text-education" : "bg-medicine/15 text-medicine"
              }`}
            >
              {a.role === "curator" ? "К" : a.name.slice(-1)}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block font-medium">{a.name}</span>
              <span className="block text-xs text-muted">{t(`hint.${a.key}`)}</span>
            </span>
            <span aria-hidden className="text-muted">
              {busy === a.key ? "…" : "→"}
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
