"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useTranslations, useLocale } from "next-intl";
import Link from "next/link";
import { api } from "@/lib/api";

type FamilyRow = { id: number; child_name: string; region: string | null; plan_status: string | null; plan_version: number | null };

export default function CuratorFamiliesPage() {
  const t = useTranslations("curator");
  const locale = useLocale();
  const [rows, setRows] = useState<FamilyRow[]>([]);
  const [inviting, setInviting] = useState(false);
  const [email, setEmail] = useState("");
  const [childName, setChildName] = useState("");

  async function reload() {
    setRows(await api.get<FamilyRow[]>("/families"));
  }

  useEffect(() => {
    reload();
  }, []);

  async function onInvite(e: FormEvent) {
    e.preventDefault();
    await api.post("/auth/invite", { email, child_name: childName });
    setEmail("");
    setChildName("");
    setInviting(false);
    reload();
  }

  const sorted = [...rows].sort((a, b) => {
    const score = (r: FamilyRow) => (r.plan_status === "draft" ? 0 : r.plan_status === null ? 1 : 2);
    return score(a) - score(b);
  });

  return (
    <main className="min-h-dvh px-6 py-10 max-w-3xl mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-medium">{t("families")}</h1>
        <button onClick={() => setInviting((v) => !v)} className="tap-target px-4 py-2 rounded-lg border border-border text-sm">
          {t("invite")}
        </button>
      </div>

      {inviting && (
        <form onSubmit={onInvite} className="flex flex-wrap gap-2 mb-6 items-end">
          <input
            required
            type="email"
            placeholder="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="tap-target rounded-lg border border-border bg-card px-3 py-2"
          />
          <input
            required
            placeholder={t("child")}
            value={childName}
            onChange={(e) => setChildName(e.target.value)}
            className="tap-target rounded-lg border border-border bg-card px-3 py-2"
          />
          <button type="submit" className="tap-target px-4 py-2 rounded-lg bg-medicine text-background text-sm">
            {t("invite")}
          </button>
        </form>
      )}

      <div className="flex flex-col gap-2">
        {sorted.map((r) => (
          <Link
            key={r.id}
            href={`/${locale}/curator/f/${r.id}`}
            className="tap-target flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3"
          >
            <span>{r.child_name}</span>
            <span className="text-sm text-muted">
              {r.plan_status === "draft" ? t("planWaiting") : r.plan_status ?? "—"}
            </span>
          </Link>
        ))}
      </div>

      <Link href={`/${locale}/curator/overdue`} className="inline-block mt-6 text-sm underline">
        {t("overdueScreen")}
      </Link>
    </main>
  );
}
