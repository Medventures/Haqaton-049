"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useTranslations, useLocale } from "next-intl";
import Link from "next/link";
import { api } from "@/lib/api";
import { AppChrome } from "@/components/AppChrome";
import { CuratorTabs } from "@/components/CuratorTabs";
import { StatusBadge } from "@/components/StatusBadge";

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
    <main className="min-h-dvh max-w-3xl mx-auto w-full">
      <AppChrome />
      <div className="px-4 sm:px-6 py-6">
      <CuratorTabs current="families" />
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">{t("families")}</h1>
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
            className={`tap-target flex items-center justify-between gap-3 rounded-xl border bg-card px-4 py-3 hover:border-medicine/60 ${
              r.plan_status === "draft" ? "border-social/60" : "border-border"
            }`}
          >
            <span className="flex items-center gap-3 min-w-0">
              <span className="flex items-center justify-center w-9 h-9 rounded-full bg-education/15 text-education text-sm font-semibold shrink-0" aria-hidden>
                {r.child_name.slice(0, 1)}
              </span>
              <span className="font-medium truncate">{r.child_name}</span>
            </span>
            {r.plan_status === "draft" ? (
              <span className="text-sm text-social shrink-0">{t("planWaiting")}</span>
            ) : r.plan_status ? (
              <StatusBadge status={r.plan_status} />
            ) : (
              <span className="text-sm text-muted shrink-0">{t("noPlan")}</span>
            )}
          </Link>
        ))}
      </div>

      </div>
    </main>
  );
}
