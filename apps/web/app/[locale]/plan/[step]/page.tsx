"use client";

import { useEffect, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { PlanJson, Step } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";

const DOC_LABEL_KEY: Record<string, string> = {
  required: "docNeed",
  if_present: "docIfPresent",
  on_request: "docOnRequest",
  agency_requests: "docAgencyRequests",
};

export default function StepPage() {
  const t = useTranslations("step");
  const locale = useLocale() as "ru" | "kk";
  const router = useRouter();
  const { step: stepId, locale: localeParam } = useParams<{ step: string; locale: string }>();
  const [step, setStep] = useState<Step | null>(null);
  const [familyId, setFamilyId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<{ id: number }>("/families/me").then((f) => {
      setFamilyId(f.id);
      api.get<PlanJson>(`/plans/${f.id}`).then((plan) => {
        setStep(plan.steps.find((s) => s.step_id === stepId) ?? null);
      });
    });
  }, [stepId]);

  async function markDone() {
    if (!familyId || !step) return;
    setBusy(true);
    try {
      const plan = await api.patch<PlanJson>(`/plans/${familyId}/steps/${step.step_id}`, { status: "done_by_parent" });
      setStep(plan.steps.find((s) => s.step_id === step.step_id) ?? null);
    } finally {
      setBusy(false);
    }
  }

  if (!step) return <main className="min-h-dvh flex items-center justify-center">…</main>;

  return (
    <main className="min-h-dvh px-6 py-10 max-w-xl mx-auto w-full">
      <button onClick={() => router.back()} className="text-sm text-muted mb-4">
        ←
      </button>
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-medium">{step[`title_${locale}`]}</h1>
        <StatusBadge status={step.status} />
      </div>
      <p className="mb-6">{step[`explanation_${locale}`]}</p>

      <dl className="grid grid-cols-2 gap-y-2 text-sm mb-6">
        <dt className="text-muted">{t("responsible")}</dt>
        <dd>{step.responsible}</dd>
        <dt className="text-muted">{t("deadline")}</dt>
        <dd>{step.deadline}</dd>
        {step.depends_on.length > 0 && (
          <>
            <dt className="text-muted">{t("dependsOn")}</dt>
            <dd>{step.depends_on.join(", ")}</dd>
          </>
        )}
      </dl>

      <h2 className="font-medium mb-2">{t("documents")}</h2>
      <ul className="flex flex-col gap-1.5 mb-6">
        {step.documents.map((d, i) => (
          <li key={i} className="flex items-center justify-between rounded-lg border border-border bg-card px-3 py-2 text-sm">
            <span>{d.doc_type}</span>
            <span className={d.in_wallet ? "text-education" : "text-muted"}>
              {d.in_wallet ? t("docHave") : t(DOC_LABEL_KEY[d.kind] ?? "docNeed")}
            </span>
          </li>
        ))}
      </ul>

      {step.source_ids.length > 0 && (
        <p className="text-xs text-muted mb-6">
          {t("basedOn")}: {step.source_ids.join(", ")}
        </p>
      )}

      {step.responsible === "parent" && !["done", "done_by_parent"].includes(step.status) && (
        <button
          onClick={markDone}
          disabled={busy}
          className="tap-target w-full rounded-lg bg-medicine text-background font-medium py-3 disabled:opacity-50"
        >
          {t("markDone")}
        </button>
      )}

      {familyId && (
        <a
          href={`/api/reports/visit/${familyId}.pdf?lang=${localeParam}&step=${step.step_id}`}
          className="block text-center text-sm underline mt-4"
        >
          PDF
        </a>
      )}
    </main>
  );
}
