"use client";

import { useTranslations } from "next-intl";
import { StatusDot } from "./icons";

const COLORS: Record<string, string> = {
  not_started: "text-muted",
  blocked: "text-muted",
  in_progress: "text-medicine",
  done_by_parent: "text-education",
  done: "text-education",
  overdue: "text-danger",
};

export function StatusBadge({ status }: { status: string }) {
  const t = useTranslations("status");
  return (
    <span className={`inline-flex items-center gap-1.5 text-sm ${COLORS[status] ?? ""}`}>
      <StatusDot status={status} className="w-4 h-4" />
      {t(status)}
    </span>
  );
}
