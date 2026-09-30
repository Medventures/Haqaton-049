"use client";

import { useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";
import { useRouter, useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";

export default function RegisterPage() {
  const t = useTranslations("auth");
  const router = useRouter();
  const { locale, token } = useParams<{ locale: string; token: string }>();
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/auth/register", { token, name, password, consent });
      router.push(`/${locale}/interview`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    }
  }

  return (
    <main className="min-h-dvh flex items-center justify-center px-6">
      <form onSubmit={onSubmit} className="w-full max-w-sm flex flex-col gap-4">
        <h1 className="text-2xl font-medium mb-2">{t("registerTitle")}</h1>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-muted">{t("name")}</span>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="tap-target rounded-lg border border-border bg-card px-3 py-2"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-muted">{t("password")}</span>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="tap-target rounded-lg border border-border bg-card px-3 py-2"
          />
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="tap-target" />
          <span className="text-sm">{t("consent")}</span>
        </label>
        {error && <p className="text-danger text-sm">{error}</p>}
        <button
          type="submit"
          disabled={!consent}
          className="tap-target rounded-lg bg-medicine text-background font-medium py-2 disabled:opacity-50"
        >
          {t("registerButton")}
        </button>
      </form>
    </main>
  );
}
