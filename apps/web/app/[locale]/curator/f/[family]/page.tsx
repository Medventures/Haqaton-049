"use client";

import { useEffect, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { PlanJson } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";

type Service = { service_id: string; title_ru: string; title_kk: string };

export default function CuratorFamilyPage() {
  const t = useTranslations("curator");
  const locale = useLocale() as "ru" | "kk";
  const { family: familyIdParam } = useParams<{ family: string }>();
  const familyId = Number(familyIdParam);
  const [plan, setPlan] = useState<PlanJson | null>(null);
  const [services, setServices] = useState<Service[]>([]);
  const [addingService, setAddingService] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    try {
      setPlan(await api.get<PlanJson>(`/plans/${familyId}`));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  }

  useEffect(() => {
    reload();
    api.get<Service[]>("/catalog/services").then(setServices);
  }, [familyId]);

  async function approve() {
    setPlan(await api.post<PlanJson>(`/plans/${familyId}/approve`));
  }

  async function addStep() {
    if (!addingService) return;
    setError(null);
    try {
      setPlan(await api.post<PlanJson>(`/plans/${familyId}/steps`, { service_id: addingService }));
      setAddingService("");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  }

  async function removeStep(stepId: string) {
    setPlan(await api.delete<PlanJson>(`/plans/${familyId}/steps/${stepId}`));
  }

  async function patchStatus(stepId: string, status: string) {
    setPlan(await api.patch<PlanJson>(`/plans/${familyId}/steps/${stepId}`, { status, comment: "curator" }));
  }

  if (error && !plan) return <main className="p-10">{error}</main>;
  if (!plan) return <main className="p-10">…</main>;

  return (
    <main className="min-h-dvh px-6 py-10 max-w-3xl mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-medium">
          C-{plan.family_id} · v{plan.version} · {plan.status}
        </h1>
        {plan.status === "draft" && (
          <button onClick={approve} className="tap-target px-4 py-2 rounded-lg bg-medicine text-background text-sm">
            {t("approve")}
          </button>
        )}
      </div>

      {error && <p className="text-danger text-sm mb-4">{error}</p>}

      <div className="flex flex-col gap-2 mb-6">
        {plan.steps.map((s) => (
          <div key={s.step_id} className="rounded-lg border border-border bg-card px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">
                  {s.step_id} · {s[`title_${locale}`]} {s.rule_id ? `(${s.rule_id})` : ""}
                </p>
                <p className="text-xs text-muted mt-0.5">
                  {s.agency} · {s.priority} · {s.deadline}
                  {s.needs_clarification && " · уточнить"}
                  {s.deadline_compressed && " · сжат"}
                </p>
              </div>
              <StatusBadge status={s.status} />
            </div>
            <div className="flex gap-2 mt-2 text-xs">
              {plan.status === "draft" && (
                <button onClick={() => removeStep(s.step_id)} className="underline text-danger">
                  {t("removeStep")}
                </button>
              )}
              {s.status !== "done" && (
                <button onClick={() => patchStatus(s.step_id, "done")} className="underline">
                  done
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {plan.status === "draft" && (
        <div className="flex gap-2">
          <select
            value={addingService}
            onChange={(e) => setAddingService(e.target.value)}
            className="tap-target rounded-lg border border-border bg-card px-3 py-2 flex-1"
          >
            <option value="">—</option>
            {services.map((s) => (
              <option key={s.service_id} value={s.service_id}>
                {s[`title_${locale}`]}
              </option>
            ))}
          </select>
          <button onClick={addStep} className="tap-target px-4 py-2 rounded-lg border border-border text-sm">
            {t("addStep")}
          </button>
        </div>
      )}
    </main>
  );
}
