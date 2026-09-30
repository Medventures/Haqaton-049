"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { PlanJson, Reference, Step } from "@/lib/types";

/** Семья, подтверждённый план и справочники родителя одним запросом-хуком. */
export function useParentData() {
  const [familyId, setFamilyId] = useState<number | null>(null);
  const [plan, setPlan] = useState<PlanJson | null>(null);
  const [reference, setReference] = useState<Reference | null>(null);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const ref = await api.get<Reference>("/catalog/reference");
        if (cancelled) return;
        setReference(ref);
        const family = await api.get<{ id: number }>("/families/me");
        if (cancelled) return;
        setFamilyId(family.id);
        setPlan(await api.get<PlanJson>(`/plans/${family.id}`));
      } catch (e) {
        if (!cancelled) setError(e as Error);
      } finally {
        if (!cancelled) setLoaded(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { familyId, plan, setPlan, reference, error, loaded };
}

export function isOpen(step: Step) {
  return step.status !== "done" && step.status !== "done_by_parent";
}

/** Разница в днях между датами ISO `YYYY-MM-DD` (раздел 11.3: даты календарные). */
export function daysBetween(fromIso: string, toIso: string) {
  const a = Date.UTC(+fromIso.slice(0, 4), +fromIso.slice(5, 7) - 1, +fromIso.slice(8, 10));
  const b = Date.UTC(+toIso.slice(0, 4), +toIso.slice(5, 7) - 1, +toIso.slice(8, 10));
  return Math.round((b - a) / 86_400_000);
}

export function formatDate(iso: string, locale: string, withYear = false) {
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleDateString(locale === "kk" ? "kk-KZ" : "ru-RU", {
    day: "numeric",
    month: "long",
    ...(withYear ? { year: "numeric" } : {}),
  });
}
