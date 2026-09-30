"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations, useLocale } from "next-intl";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { PlanJson } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";
import { ArrowLink } from "@/components/ParentNav";
import { DownloadButton } from "@/components/FileButton";
import { AppChrome } from "@/components/AppChrome";
import { daysBetween, formatDate, useParentData } from "@/lib/parent";
import { downloadIcs } from "@/lib/ics";

const DOC_LABEL_KEY: Record<string, string> = {
  required: "docNeed",
  if_present: "docIfPresent",
  on_request: "docOnRequest",
  agency_requests: "docAgencyRequests",
};

export default function StepPage() {
  const t = useTranslations("step");
  const tH = useTranslations("hint");
  const tN = useTranslations("nav");
  const tR = useTranslations("reminders");
  const tResp = useTranslations("responsible");
  const tPdf = useTranslations("pdf");
  const locale = useLocale() as "ru" | "kk";
  const { step: stepId, locale: localeParam } = useParams<{ step: string; locale: string }>();
  const { familyId, plan, setPlan, reference } = useParentData();
  const [busy, setBusy] = useState(false);

  const steps = plan?.steps ?? [];
  const idx = steps.findIndex((s) => s.step_id === stepId);
  const step = idx >= 0 ? steps[idx] : null;

  async function markDone() {
    if (!familyId || !step) return;
    setBusy(true);
    try {
      setPlan(await api.patch<PlanJson>(`/plans/${familyId}/steps/${step.step_id}`, { status: "done_by_parent" }));
    } finally {
      setBusy(false);
    }
  }

  if (!step || !reference) return <main className="min-h-dvh flex items-center justify-center">…</main>;

  const prev = idx > 0 ? steps[idx - 1] : null;
  const next = idx < steps.length - 1 ? steps[idx + 1] : null;
  const stepHref = (id: string) => `/${locale}/plan/${id}`;
  const left = step.deadline ? daysBetween(reference.today, step.deadline) : null;
  const toBring = step.documents.filter((d) => d.kind === "required" || d.kind === "if_present");
  const providers = step.provider_ids.map((id) => reference.providers[id]).filter(Boolean);
  const deps = step.depends_on.map((id) => steps.find((s) => s.step_id === id)).filter(Boolean);
  const docTitle = (docType: string) => reference.document_types[docType]?.[`title_${locale}`] ?? docType;

  return (
    <main className="min-h-dvh">
      <AppChrome />
      <div className="max-w-xl mx-auto w-full px-4 sm:px-6 pt-4">
      <Link href={`/${locale}/plan`} className="tap-target inline-flex items-center gap-1 text-sm text-muted mb-4 min-h-11">
        ← {tN("toPlan")}
      </Link>
      <p className="text-xs text-muted mb-1">{tN("stepOf", { n: idx + 1, total: steps.length })}</p>
      <div className="flex items-start justify-between gap-3 mb-2">
        <h1 className="text-2xl font-medium">{step[`title_${locale}`]}</h1>
        <StatusBadge status={step.status} />
      </div>
      <p className={`text-sm mb-6 ${left !== null && left < 0 ? "text-danger" : "text-muted"}`}>
        {step.deadline ? (
          <>
            {tH("deadlineIn", { date: formatDate(step.deadline, locale, true) })} ·{" "}
            {left! < 0 ? tR("overdueDays", { n: -left! }) : left === 0 ? tR("todayDue") : tR("inDays", { n: left! })}
          </>
        ) : (
          tH("noDeadline")
        )}
      </p>

      <section className="rounded-xl border border-border bg-card p-4 mb-6" aria-labelledby="hint-title">
        <h2 id="hint-title" className="font-medium mb-3 flex items-center gap-2">
          <svg viewBox="0 0 24 24" className="w-5 h-5 text-social" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <circle cx="12" cy="10" r="6" />
            <path d="M9 20h6M10 16v4M14 16v4" />
          </svg>
          {tH("title")}
        </h2>

        <h3 className="text-sm text-muted">{tH("what")}</h3>
        <p className="mb-4">{step[`explanation_${locale}`]}</p>

        {deps.length > 0 && (
          <>
            <h3 className="text-sm text-muted">{tH("first")}</h3>
            <ul className="mb-4">
              {deps.map((d) => (
                <li key={d!.step_id}>
                  <Link href={stepHref(d!.step_id)} className="underline">
                    {d![`title_${locale}`]}
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}

        <h3 className="text-sm text-muted mb-1">{tH("bring")}</h3>
        {toBring.length === 0 && <p className="mb-4">{tH("nothingToBring")}</p>}
        <ul className="flex flex-col gap-1.5 mb-4">
          {toBring.map((d, i) => (
            <li key={i} className="flex items-center justify-between gap-3 rounded-lg border border-border px-3 py-2 text-sm">
              <span>{docTitle(d.doc_type)}</span>
              <span className={`shrink-0 ${d.in_wallet ? "text-education" : "text-muted"}`}>
                {d.in_wallet ? `✓ ${t("docHave")}` : t(DOC_LABEL_KEY[d.kind] ?? "docNeed")}
              </span>
            </li>
          ))}
        </ul>

        {providers.length > 0 && (
          <>
            <h3 className="text-sm text-muted mb-1">{tH("where")}</h3>
            {providers.map((p) => (
              <div key={p.provider_id} className="text-sm mb-2">
                <p className="font-medium">{p[`name_${locale}`]}</p>
                {p[`address_${locale}`] && <p>{p[`address_${locale}`]}</p>}
                {p.phone && (
                  <p>
                    {tH("phone")}:{" "}
                    <a href={`tel:${p.phone.replace(/[^\d+]/g, "")}`} className="underline">
                      {p.phone}
                    </a>
                  </p>
                )}
                {p[`hours_${locale}`] && (
                  <p className="text-muted">
                    {tH("hours")}: {p[`hours_${locale}`]}
                  </p>
                )}
              </div>
            ))}
          </>
        )}
      </section>

      {step.documents.some((d) => d.kind === "on_request" || d.kind === "agency_requests") && (
        <>
          <h2 className="font-medium mb-2">{t("documents")}</h2>
          <ul className="flex flex-col gap-1.5 mb-6">
            {step.documents
              .filter((d) => d.kind === "on_request" || d.kind === "agency_requests")
              .map((d, i) => (
                <li key={i} className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card px-3 py-2 text-sm">
                  <span>{docTitle(d.doc_type)}</span>
                  <span className="text-muted shrink-0">{t(DOC_LABEL_KEY[d.kind])}</span>
                </li>
              ))}
          </ul>
        </>
      )}

      <dl className="grid grid-cols-2 gap-y-2 text-sm mb-6">
        <dt className="text-muted">{t("responsible")}</dt>
        <dd>{tResp(step.responsible)}</dd>
      </dl>

      {step.source_ids.length > 0 && (
        <p className="text-xs text-muted mb-6">
          {t("basedOn")}: {step.source_ids.join(", ")}
        </p>
      )}

      <div className="flex flex-col gap-3">
        {step.responsible === "parent" && !["done", "done_by_parent"].includes(step.status) && (
          <button
            onClick={markDone}
            disabled={busy}
            className="tap-target w-full rounded-lg bg-medicine text-background font-medium py-3 disabled:opacity-50"
          >
            {t("markDone")}
          </button>
        )}
        {step.deadline && (
          <button
            onClick={() => downloadIcs([step], locale, `adm-${step.step_id}.ics`)}
            className="tap-target w-full rounded-lg border border-border bg-card py-3 text-sm"
          >
            {tH("addToCalendar")}
          </button>
        )}
        {familyId && (
          <DownloadButton
            href={`/api/reports/visit/${familyId}.pdf?lang=${localeParam}&step=${step.step_id}`}
            title={tPdf("visit")}
          />
        )}
      </div>

      </div>
      <div aria-hidden className="h-24" />
      <nav
        aria-label={tN("label")}
        className="fixed bottom-0 inset-x-0 z-40 border-t border-border bg-background/95 backdrop-blur pb-[env(safe-area-inset-bottom)]"
      >
        <div className="max-w-xl mx-auto flex items-center gap-2 px-3 py-2">
          <ArrowLink href={prev ? stepHref(prev.step_id) : null} dir="prev" label={tN("prevStep")} />
          <p className="flex-1 text-center text-sm">
            {tN("stepOf", { n: idx + 1, total: steps.length })}
          </p>
          <ArrowLink href={next ? stepHref(next.step_id) : null} dir="next" label={tN("nextStep")} />
        </div>
      </nav>
    </main>
  );
}
