"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";

/** Самостоятельная регистрация родителя (без приглашения куратора). */
export default function RegisterPage() {
  const t = useTranslations("auth");
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [childName, setChildName] = useState("");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.post("/auth/signup", { name, email, password, child_name: childName, consent });
      router.push(`/${locale}/interview`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) setError(t("emailTaken"));
      // Короткие сообщения сервера («Пароль должен быть…») понятны, технические — нет.
      else if (err instanceof ApiError && err.status === 422 && err.message.length < 100) setError(err.message);
      else setError(t("signupError"));
    } finally {
      setLoading(false);
    }
  }

  const field = "tap-target rounded-xl border border-border bg-background px-3 py-2";

  return (
    <main className="min-h-dvh flex flex-col items-center justify-center gap-4 px-4 py-8">
      <form onSubmit={onSubmit} className="w-full max-w-sm flex flex-col gap-4 rounded-2xl border border-border bg-card p-6">
        <Link href={`/${locale}`} className="font-semibold tracking-tight text-muted text-sm">
          ADM
        </Link>
        <div>
          <h1 className="text-2xl font-semibold mb-1">{t("signupTitle")}</h1>
          <p className="text-sm text-muted">{t("signupSubtitle")}</p>
        </div>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-muted">{t("name")}</span>
          <input required autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} className={field} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-muted">{t("email")}</span>
          <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className={field} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-muted">{t("password")}</span>
          <input
            type="password"
            required
            minLength={6}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={field}
          />
          <span className="text-xs text-muted">{t("passwordHint")}</span>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-muted">{t("childName")}</span>
          <input required value={childName} onChange={(e) => setChildName(e.target.value)} className={field} />
        </label>
        <label className="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="w-5 h-5 accent-[var(--color-medicine)]" />
          <span className="text-sm">{t("consent")}</span>
        </label>
        {error && <p className="text-danger text-sm">{error}</p>}
        <button
          type="submit"
          disabled={loading || !consent}
          className="tap-target rounded-xl bg-medicine text-background font-medium py-3 disabled:opacity-50"
        >
          {t("createAccount")}
        </button>
        <p className="text-sm text-muted text-center">
          {t("haveAccount")}{" "}
          <Link href={`/${locale}/login`} className="underline text-foreground">
            {t("loginButton")}
          </Link>
        </p>
      </form>
    </main>
  );
}
