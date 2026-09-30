"use client";

import { useEffect, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import Link from "next/link";
import { api } from "@/lib/api";

type Row = { family_id: number; child_name: string; step_id: string; service_id: string; agency: string; deadline: string; escalation_level: number };

export default function OverduePage() {
  const t = useTranslations("curator");
  const locale = useLocale();
  const [rows, setRows] = useState<Row[]>([]);

  useEffect(() => {
    api.get<Row[]>("/overdue").then(setRows);
  }, []);

  return (
    <main className="min-h-dvh px-6 py-10 max-w-3xl mx-auto w-full">
      <h1 className="text-2xl font-medium mb-6">{t("overdueScreen")}</h1>
      <div className="flex flex-col gap-2">
        {rows.map((r, i) => (
          <Link
            key={i}
            href={`/${locale}/curator/f/${r.family_id}`}
            className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3"
          >
            <span>
              {r.child_name} · {r.service_id}
            </span>
            <span className="text-danger text-sm">
              {r.agency} · уровень {r.escalation_level}
            </span>
          </Link>
        ))}
        {rows.length === 0 && <p className="text-muted">—</p>}
      </div>
    </main>
  );
}
