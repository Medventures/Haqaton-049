"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { AppChrome } from "@/components/AppChrome";
import { ParentNav } from "@/components/ParentNav";
import { StatusBadge } from "@/components/StatusBadge";
import { daysBetween, formatDate, isOpen, monthName, useParentData } from "@/lib/parent";
import { downloadIcs } from "@/lib/ics";
import type { Step } from "@/lib/types";

const AGENCY_BG: Record<Step["agency"], string> = {
  medicine: "bg-medicine",
  education: "bg-education",
  social: "bg-social",
};

function iso(y: number, m: number, d: number) {
  return `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

export default function CalendarPage() {
  const t = useTranslations("calendar");
  const tR = useTranslations("reminders");
  const locale = useLocale() as "ru" | "kk";
  const router = useRouter();
  const { plan, reference, error, loaded } = useParentData();
  const today = reference?.today ?? null;
  const [month, setMonth] = useState<{ y: number; m: number } | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    if (!today || !plan || month) return;
    // Текущий месяц, если в нём есть открытые сроки, иначе месяц ближайшего срока.
    const upcomingDates = plan.steps
      .filter((s) => s.deadline && isOpen(s))
      .map((s) => s.deadline!)
      .sort();
    const thisMonth = today.slice(0, 7);
    const target =
      upcomingDates.some((d) => d.startsWith(thisMonth)) || !upcomingDates.length
        ? today
        : upcomingDates.find((d) => d >= today) ?? upcomingDates[upcomingDates.length - 1];
    setMonth({ y: +target.slice(0, 4), m: +target.slice(5, 7) - 1 });
  }, [today, plan, month]);

  useEffect(() => {
    // Без подтверждённого плана календарь пуст: ведём туда, где план появится.
    if (loaded && error) router.replace(`/${locale}/plan`);
  }, [loaded, error, router, locale]);

  const byDate = useMemo(() => {
    const map: Record<string, Step[]> = {};
    for (const s of plan?.steps ?? []) if (s.deadline) (map[s.deadline] ||= []).push(s);
    return map;
  }, [plan]);

  if (!plan || !today || !month) {
    return (
      <main className="min-h-dvh flex items-center justify-center">…</main>
    );
  }

  const first = new Date(Date.UTC(month.y, month.m, 1));
  const daysInMonth = new Date(Date.UTC(month.y, month.m + 1, 0)).getUTCDate();
  const lead = (first.getUTCDay() + 6) % 7; // понедельник первым
  const cells: (string | null)[] = [...Array(lead).fill(null)];
  for (let d = 1; d <= daysInMonth; d++) cells.push(iso(month.y, month.m, d));
  while (cells.length % 7) cells.push(null);

  const name = monthName(month.m, locale);
  const monthTitle = `${name.charAt(0).toUpperCase()}${name.slice(1)} ${month.y}`;
  const shift = (delta: number) => {
    const m = month.m + delta;
    setMonth({ y: month.y + Math.floor(m / 12), m: ((m % 12) + 12) % 12 });
    setSelected(null);
  };

  const upcoming = plan.steps
    .filter((s) => s.deadline && isOpen(s))
    .sort((a, b) => a.deadline!.localeCompare(b.deadline!));
  const list = selected ? byDate[selected] ?? [] : upcoming;

  return (
    <main className="min-h-dvh max-w-2xl mx-auto w-full">
      <AppChrome />
      <div className="px-4 sm:px-6 pb-6">
        <h1 className="text-2xl font-semibold pt-6 mb-4">{t("title")}</h1>

        <div className="flex items-center justify-between mb-2">
          <button onClick={() => shift(-1)} aria-label={t("prevMonth")} className="tap-target min-w-11 min-h-11 rounded-lg border border-border">
            ‹
          </button>
          <p className="font-medium">{monthTitle}</p>
          <button onClick={() => shift(1)} aria-label={t("nextMonth")} className="tap-target min-w-11 min-h-11 rounded-lg border border-border">
            ›
          </button>
        </div>

        <div className="grid grid-cols-7 text-center text-xs text-muted mb-1">
          {t("weekdays").split(",").map((w) => (
            <span key={w}>{w}</span>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1 mb-6">
          {cells.map((day, i) => {
            if (!day) return <span key={i} />;
            const steps = byDate[day] ?? [];
            const overdue = steps.some((s) => s.status === "overdue");
            const isToday = day === today;
            const isSel = day === selected;
            return (
              <button
                key={day}
                onClick={() => setSelected(isSel ? null : day)}
                aria-pressed={isSel}
                aria-label={`${formatDate(day, locale)}${steps.length ? `: ${steps.map((s) => s[`title_${locale}`]).join(", ")}` : ""}`}
                className={`min-h-11 rounded-lg flex flex-col items-center justify-center gap-0.5 text-sm border ${
                  isSel ? "border-foreground" : isToday ? "border-medicine" : "border-transparent"
                } ${steps.length ? "bg-card" : ""} ${overdue ? "text-danger" : ""}`}
              >
                <span className={isToday ? "font-semibold" : ""}>{+day.slice(8)}</span>
                <span className="flex gap-0.5 h-1.5">
                  {steps.slice(0, 3).map((s) => (
                    <span key={s.step_id} className={`w-1.5 h-1.5 rounded-full ${s.status === "overdue" ? "bg-danger" : AGENCY_BG[s.agency]}`} />
                  ))}
                </span>
              </button>
            );
          })}
        </div>

        <h2 className="text-lg font-medium mb-3">{selected ? formatDate(selected, locale, true) : t("upcoming")}</h2>
        <div className="flex flex-col gap-2 mb-6">
          {list.length === 0 && <p className="text-muted">{t("noDeadlines")}</p>}
          {list.map((s) => {
            const left = daysBetween(today, s.deadline!);
            return (
              <Link
                key={s.step_id}
                href={`/${locale}/plan/${s.step_id}`}
                className="tap-target flex items-center justify-between gap-3 rounded-lg border border-border bg-card px-4 py-3"
              >
                <span className="flex items-start gap-3 min-w-0">
                  <span className={`mt-1.5 w-2.5 h-2.5 rounded-full shrink-0 ${AGENCY_BG[s.agency]}`} />
                  <span className="min-w-0">
                    <span className="block font-medium">{s[`title_${locale}`]}</span>
                    <span className={`block text-xs ${left < 0 ? "text-danger" : "text-muted"}`}>
                      {formatDate(s.deadline!, locale)} ·{" "}
                      {left < 0 ? tR("overdueDays", { n: -left }) : left === 0 ? tR("todayDue") : tR("inDays", { n: left })}
                    </span>
                  </span>
                </span>
                <StatusBadge status={s.status} />
              </Link>
            );
          })}
        </div>

        {upcoming.length > 0 && (
          <button
            onClick={() => downloadIcs(upcoming, locale, "adm.ics")}
            className="tap-target w-full rounded-lg border border-border bg-card px-4 py-3 text-sm"
          >
            <span className="block font-medium">{t("addAll")}</span>
            <span className="block text-xs text-muted">{t("addAllHint")}</span>
          </button>
        )}
      </div>
      <ParentNav current="calendar" />
    </main>
  );
}
