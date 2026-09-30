"use client";

import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";

/** Переключатель разделов куратора: «Мои семьи» и «Просрочки». */
export function CuratorTabs({ current }: { current: "families" | "overdue" }) {
  const t = useTranslations("curator");
  const locale = useLocale();
  const tabs = [
    { key: "families", href: `/${locale}/curator`, label: t("families") },
    { key: "overdue", href: `/${locale}/curator/overdue`, label: t("overdueScreen") },
  ] as const;
  return (
    <nav className="inline-flex rounded-xl border border-border bg-card p-1 mb-6">
      {tabs.map((tab) => (
        <Link
          key={tab.key}
          href={tab.href}
          aria-current={tab.key === current ? "page" : undefined}
          className={`tap-target flex items-center rounded-lg px-4 text-sm ${
            tab.key === current ? "bg-background font-medium" : "text-muted"
          }`}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
}
