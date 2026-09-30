import type { Step } from "@/lib/types";

/**
 * Файл .ics со сроками шагов: телефон добавляет их в свой календарь вместе
 * с напоминаниями за 3 дня и за 1 день (в 9:00).
 */
export function buildIcs(steps: Step[], locale: "ru" | "kk", origin: string): string {
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  const esc = (s: string) => s.replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/[,;]/g, (m) => `\\${m}`);
  const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AqylRoute//RU", "CALSCALE:GREGORIAN"];
  for (const s of steps) {
    if (!s.deadline) continue;
    const day = s.deadline.replace(/-/g, "");
    const title = s[`title_${locale}`];
    const url = `${origin}/${locale}/plan/${s.step_id}`;
    lines.push(
      "BEGIN:VEVENT",
      `UID:aqylroute-${s.step_id}-${day}@aqylroute`,
      `DTSTAMP:${stamp}`,
      `DTSTART;VALUE=DATE:${day}`,
      `SUMMARY:${esc(`AqylRoute: ${title}`)}`,
      `DESCRIPTION:${esc(`${s[`explanation_${locale}`] ?? ""}\n${url}`)}`,
      `URL:${url}`,
      "BEGIN:VALARM",
      "ACTION:DISPLAY",
      `DESCRIPTION:${esc(title)}`,
      "TRIGGER:-P2DT15H",
      "END:VALARM",
      "BEGIN:VALARM",
      "ACTION:DISPLAY",
      `DESCRIPTION:${esc(title)}`,
      "TRIGGER:-PT15H",
      "END:VALARM",
      "END:VEVENT",
    );
  }
  lines.push("END:VCALENDAR");
  return lines.join("\r\n");
}

export function downloadIcs(steps: Step[], locale: "ru" | "kk", filename: string) {
  const blob = new Blob([buildIcs(steps, locale, window.location.origin)], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
