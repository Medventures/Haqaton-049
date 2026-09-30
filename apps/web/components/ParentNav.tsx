"use client";

import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";

export const PARENT_SCREENS = ["plan", "calendar", "notifications", "documents"] as const;
export type ParentScreen = (typeof PARENT_SCREENS)[number];

/**
 * Нижняя навигация родителя для телефона: экраны идут сценарием
 * «План → Календарь → Напоминания → Документы», стрелки листают по порядку,
 * точки ведут на экран напрямую.
 */
export function ParentNav({ current }: { current: ParentScreen }) {
  const t = useTranslations("nav");
  const locale = useLocale();
  const idx = PARENT_SCREENS.indexOf(current);
  const prev = idx > 0 ? PARENT_SCREENS[idx - 1] : null;
  const next = idx < PARENT_SCREENS.length - 1 ? PARENT_SCREENS[idx + 1] : null;
  const href = (s: ParentScreen) => `/${locale}/${s}`;

  return (
    <>
      <div aria-hidden className="h-28" />
      <nav
        aria-label={t("label")}
        className="fixed bottom-0 inset-x-0 z-40 border-t border-border bg-background/95 backdrop-blur pb-[env(safe-area-inset-bottom)]"
      >
        <div className="max-w-2xl mx-auto flex items-center gap-2 px-3 py-2">
          <ArrowLink href={prev ? href(prev) : null} dir="prev" label={prev ? t(prev) : ""} />
          <div className="flex-1 min-w-0 text-center">
            <p className="text-sm font-medium truncate">
              {t(current)} <span className="text-muted font-normal">· {idx + 1}/{PARENT_SCREENS.length}</span>
            </p>
            <p className="text-xs text-muted truncate">{t(`${current}Hint`)}</p>
            <div className="flex justify-center gap-1 mt-1">
              {PARENT_SCREENS.map((s) => (
                <Link
                  key={s}
                  href={href(s)}
                  aria-label={t(s)}
                  aria-current={s === current ? "page" : undefined}
                  className="p-1.5 -m-0.5"
                >
                  <span className={`block w-2 h-2 rounded-full ${s === current ? "bg-foreground" : "bg-border"}`} />
                </Link>
              ))}
            </div>
          </div>
          <ArrowLink href={next ? href(next) : null} dir="next" label={next ? t(next) : ""} />
        </div>
      </nav>
    </>
  );
}

export function ArrowLink({ href, dir, label }: { href: string | null; dir: "prev" | "next"; label: string }) {
  const arrow = (
    <svg viewBox="0 0 24 24" className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      {dir === "prev" ? <path d="M15 5l-7 7 7 7" /> : <path d="M9 5l7 7-7 7" />}
    </svg>
  );
  const cls = "tap-target flex items-center justify-center rounded-lg border border-border w-12 h-12 shrink-0";
  if (!href) return <span className={`${cls} opacity-30`} aria-hidden>{arrow}</span>;
  return (
    <Link href={href} className={`${cls} bg-card`} aria-label={label} title={label}>
      {arrow}
    </Link>
  );
}
