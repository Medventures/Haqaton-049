"use client";

import { useEffect, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { PlanJson } from "@/lib/types";
import { AGENCY_ICON } from "@/components/icons";
import { StatusBadge } from "@/components/StatusBadge";
import { AppChrome } from "@/components/AppChrome";

export default function PlanPage() {
  const t = useTranslations("plan");
  const tAgency = useTranslations("agency");
  const locale = useLocale() as "ru" | "kk";
  const router = useRouter();
  const [family, setFamily] = useState<{ id: number } | null>(null);
  const [plan, setPlan] = useState<PlanJson | null | "draft">(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<{ id: number }>("/families/me")
      .then((f) => {
        setFamily(f);
        return api.get<PlanJson>(`/plans/${f.id}`);
      })
      .then(setPlan)
      .catch((e) => {
        if (e instanceof ApiError && e.code === "no_plan") {
          router.replace(`/${locale}/interview`);
        } else if (e instanceof ApiError && e.status === 404) {
          setPlan(e.code === "not_found" ? "draft" : null);
        } else {
          setError(String(e));
        }
      });
  }, []);

  if (error) return <Centered>{error}</Centered>;
  if (family === null) return <Centered>…</Centered>;
  if (plan === "draft") return <WaitingScreen />;
  if (!plan) return <Centered>…</Centered>;

  const notDone = plan.steps.filter((s) => s.status !== "done" && s.status !== "blocked");
  const thisWeek = notDone.slice(0, 3);
  const byAgency: Record<string, typeof plan.steps> = { medicine: [], education: [], social: [] };
  for (const s of plan.steps) byAgency[s.agency]?.push(s);

  return (
    <main className="min-h-dvh max-w-2xl mx-auto w-full">
      <AppChrome />
      <div className="px-6 pb-10">
      <div className="flex justify-between items-center mb-6 pt-4">
        <h1 className="text-2xl font-medium">AqylRoute</h1>
        <a href={`/api/reports/route/${family.id}.pdf?lang=${locale}`} className="text-sm underline">
          скачать PDF
        </a>
      </div>

      <section className="mb-8">
        <h2 className="text-lg font-medium mb-3">{t("thisWeek")}</h2>
        <div className="flex flex-col gap-2">
          {thisWeek.length === 0 && <p className="text-muted">{t("empty")}</p>}
          {thisWeek.map((s) => (
            <StepRow key={s.step_id} step={s} familyId={family.id} locale={locale} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-medium mb-3">{t("route")}</h2>
        {(["medicine", "education", "social"] as const).map((agency) => {
          const Icon = AGENCY_ICON[agency];
          const steps = byAgency[agency];
          if (!steps.length) return null;
          return (
            <div key={agency} className="mb-5">
              <div className="flex items-center gap-2 mb-2 text-sm text-muted">
                <Icon className={`w-4 h-4 text-${agency}`} />
                {tAgency(agency)}
              </div>
              <div className="flex flex-col gap-2">
                {steps.map((s) => (
                  <StepRow key={s.step_id} step={s} familyId={family.id} locale={locale} />
                ))}
              </div>
            </div>
          );
        })}
      </section>
      </div>
    </main>
  );
}

function StepRow({ step, familyId, locale }: { step: PlanJson["steps"][number]; familyId: number; locale: "ru" | "kk" }) {
  const t = useTranslations("plan");
  return (
    <Link
      href={`/${locale}/plan/${step.step_id}`}
      className="tap-target flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3"
    >
      <div>
        <p className="font-medium">{step[`title_${locale}`]}</p>
        {step.status === "overdue" && step.deadline !== step.original_deadline && (
          <p className="text-xs text-danger mt-0.5">
            {t("wasLabel")} {step.original_deadline} → {t("nowLabel")} {step.deadline}
          </p>
        )}
      </div>
      <StatusBadge status={step.status} />
    </Link>
  );
}

function WaitingScreen() {
  const t = useTranslations("interview");
  return (
    <>
      <AppChrome />
      <Centered>
        <h1 className="text-2xl font-medium mb-2">{t("waitingTitle")}</h1>
        <p className="text-muted">{t("waitingBody")}</p>
      </Centered>
    </>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return <main className="min-h-dvh flex flex-col items-center justify-center px-6 text-center gap-2">{children}</main>;
}
