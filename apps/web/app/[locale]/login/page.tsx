"use client";

import { useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";
import { useRouter, useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";

export default function LoginPage() {
  const t = useTranslations("auth");
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await api.post<{ role: string }>("/auth/login", { email, password });
      router.push(user.role === "curator" ? `/${locale}/curator` : `/${locale}/plan`);
    } catch (err) {
      setError(err instanceof ApiError ? t("invalidCredentials") : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-dvh flex items-center justify-center px-6">
      <form onSubmit={onSubmit} className="w-full max-w-sm flex flex-col gap-4">
        <h1 className="text-2xl font-medium mb-2">{t("loginTitle")}</h1>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-muted">{t("email")}</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="tap-target rounded-lg border border-border bg-card px-3 py-2"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-muted">{t("password")}</span>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="tap-target rounded-lg border border-border bg-card px-3 py-2"
          />
        </label>
        {error && <p className="text-danger text-sm">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="tap-target rounded-lg bg-medicine text-background font-medium py-2 disabled:opacity-50"
        >
          {t("loginButton")}
        </button>
      </form>
    </main>
  );
}
