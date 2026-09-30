"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { AppChrome } from "@/components/AppChrome";
import { ParentNav } from "@/components/ParentNav";
import { daysBetween, formatDate, isOpen, useParentData } from "@/lib/parent";
import type { Step } from "@/lib/types";

type Notif = { id: number; type: string; payload: Record<string, unknown>; created_at: string; read_at: string | null };

const SOON_DAYS = 21;

export default function NotificationsPage() {
  const t = useTranslations("notifications");
  const tR = useTranslations("reminders");
  const locale = useLocale() as "ru" | "kk";
  const { plan, reference } = useParentData();
  const [items, setItems] = useState<Notif[]>([]);

  async function reload() {
    setItems(await api.get<Notif[]>("/notifications"));
  }

  useEffect(() => {
    reload();
  }, []);

  async function markAllRead() {
    const unread = items.filter((n) => !n.read_at).map((n) => n.id);
    if (!unread.length) return;
    await api.post("/notifications/read", { ids: unread });
    await reload();
  }

  const today = reference?.today;
  const open = (plan?.steps ?? []).filter((s) => s.deadline && isOpen(s) && s.status !== "blocked");
  const overdue = today ? open.filter((s) => daysBetween(today, s.deadline!) < 0 || s.status === "overdue") : [];
  const soon = today
    ? open
        .filter((s) => !overdue.includes(s) && daysBetween(today, s.deadline!) <= SOON_DAYS)
        .sort((a, b) => a.deadline!.localeCompare(b.deadline!))
    : [];
  const stepById = Object.fromEntries((plan?.steps ?? []).map((s) => [s.step_id, s]));
  const typeLabel = (type: string) => (tR.has(`types.${type}`) ? tR(`types.${type}`) : type);

  return (
    <main className="min-h-dvh max-w-2xl mx-auto w-full">
      {plan && <AppChrome />}
      <div className="px-4 sm:px-6 pb-6">
        <h1 className="text-2xl font-medium pt-4 mb-6">{t("title")}</h1>

        {plan && today && (
          <>
            {overdue.length > 0 && (
              <Section title={tR("overdue")} danger>
                {overdue.map((s) => (
                  <StepReminder key={s.step_id} step={s} today={today} locale={locale} />
                ))}
              </Section>
            )}
            <Section title={tR("soon")}>
              {soon.length === 0 && <p className="text-muted text-sm">{tR("nothingSoon")}</p>}
              {soon.map((s) => (
                <StepReminder key={s.step_id} step={s} today={today} locale={locale} />
              ))}
            </Section>
          </>
        )}

        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-medium">{tR("feed")}</h2>
          {items.some((n) => !n.read_at) && (
            <button onClick={markAllRead} className="tap-target text-sm underline">
              {t("markRead")}
            </button>
          )}
        </div>
        <div className="flex flex-col gap-2">
          {items.length === 0 && <p className="text-muted">{t("empty")}</p>}
          {items.map((n) => {
            const step = typeof n.payload.step_id === "string" ? stepById[n.payload.step_id] : undefined;
            const body = (
              <>
                <p className="font-medium flex items-center gap-2">
                  {!n.read_at && <span className="w-2 h-2 rounded-full bg-medicine shrink-0" aria-hidden />}
                  {typeLabel(n.type)}
                </p>
                {step && <p className="mt-0.5">{step[`title_${locale}`]}</p>}
                <p className="text-muted text-xs mt-1">{new Date(n.created_at).toLocaleString(locale === "kk" ? "kk-KZ" : "ru-RU")}</p>
              </>
            );
            const cls = `block rounded-lg border border-border px-4 py-3 text-sm ${n.read_at ? "opacity-60" : "bg-card"}`;
            return step ? (
              <Link key={n.id} href={`/${locale}/plan/${step.step_id}`} className={cls}>
                {body}
              </Link>
            ) : (
              <div key={n.id} className={cls}>
                {body}
              </div>
            );
          })}
        </div>
      </div>
      {plan && <ParentNav current="notifications" />}
    </main>
  );
}

function Section({ title, danger, children }: { title: string; danger?: boolean; children: React.ReactNode }) {
  return (
    <section className="mb-6">
      <h2 className={`text-lg font-medium mb-3 ${danger ? "text-danger" : ""}`}>{title}</h2>
      <div className="flex flex-col gap-2">{children}</div>
    </section>
  );
}

function StepReminder({ step, today, locale }: { step: Step; today: string; locale: "ru" | "kk" }) {
  const tR = useTranslations("reminders");
  const left = daysBetween(today, step.deadline!);
  return (
    <Link
      href={`/${locale}/plan/${step.step_id}`}
      className={`tap-target block rounded-lg border px-4 py-3 bg-card ${left < 0 ? "border-danger" : "border-border"}`}
    >
      <p className="font-medium">{step[`title_${locale}`]}</p>
      <p className={`text-xs mt-0.5 ${left < 0 ? "text-danger" : "text-muted"}`}>
        {formatDate(step.deadline!, locale)} ·{" "}
        {left < 0 ? tR("overdueDays", { n: -left }) : left === 0 ? tR("todayDue") : tR("inDays", { n: left })}
      </p>
    </Link>
  );
}
