"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";

type Me = { id: number; role: "parent" | "curator"; name: string; email: string };

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("");
}

/** Шапка: логотип, помощь (FAQ) и профиль с именем, темой, языком и выходом. */
export function AppHeader() {
  const t = useTranslations("header");
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const [me, setMe] = useState<Me | null>(null);
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get<Me>("/auth/me").then(setMe).catch(() => setMe(null));
    setTheme(document.documentElement.dataset.theme === "light" ? "light" : "dark");
  }, []);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!menuRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch {
      // приватный режим: тема не запомнится
    }
  }

  async function logout() {
    navigator.serviceWorker?.controller?.postMessage("LOGOUT_CLEAR_PRIVATE_CACHE");
    await api.post("/auth/logout");
    router.push(`/${locale}`);
  }

  const otherLocale = locale === "ru" ? "kk" : "ru";
  const switchLocaleHref = pathname.replace(/^\/(ru|kk)(?=\/|$)/, `/${otherLocale}`);
  const home = me ? (me.role === "curator" ? `/${locale}/curator` : `/${locale}/plan`) : `/${locale}`;

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/95 backdrop-blur">
      <div className="max-w-5xl mx-auto flex items-center gap-2 px-4 h-14">
        <Link href={home} className="flex items-center gap-2 font-semibold tracking-tight mr-auto">
          <svg viewBox="0 0 24 24" className="w-6 h-6" aria-hidden>
            <circle cx="5" cy="17" r="3" className="fill-medicine" />
            <circle cx="12" cy="7" r="3" className="fill-education" />
            <circle cx="19" cy="17" r="3" className="fill-social" />
            <path d="M5 17 12 7l7 10" fill="none" stroke="currentColor" strokeWidth="1.5" opacity=".5" />
          </svg>
          ADM
        </Link>

        <Link
          href={`/${locale}/faq`}
          aria-label={t("faq")}
          title={t("faq")}
          className="tap-target flex items-center justify-center rounded-full border border-border text-sm font-medium w-11 h-11"
        >
          ?
        </Link>

        {me && (
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setOpen((o) => !o)}
              aria-expanded={open}
              aria-haspopup="menu"
              className="tap-target flex items-center gap-2 rounded-full border border-border pl-1 pr-3 h-11"
            >
              <span className="flex items-center justify-center w-9 h-9 rounded-full bg-medicine/20 text-medicine text-sm font-semibold">
                {initials(me.name) || "?"}
              </span>
              <span className="text-left leading-tight max-w-[9rem]">
                <span className="block text-sm font-medium truncate">{me.name}</span>
                <span className="block text-xs text-muted">{t(`role.${me.role}`)}</span>
              </span>
            </button>

            {open && (
              <div role="menu" className="absolute right-0 mt-2 w-64 rounded-xl border border-border bg-card shadow-lg p-2 text-sm">
                <div className="px-3 py-2 border-b border-border mb-1">
                  <p className="font-medium">{me.name}</p>
                  <p className="text-xs text-muted truncate">{me.email}</p>
                </div>
                <MenuLink href={`/${locale}/faq`} onClick={() => setOpen(false)}>
                  {t("faq")}
                </MenuLink>
                <button role="menuitem" onClick={toggleTheme} className="tap-target w-full text-left rounded-lg px-3 hover:bg-background">
                  {theme === "dark" ? t("lightTheme") : t("darkTheme")}
                </button>
                <MenuLink href={switchLocaleHref} onClick={() => setOpen(false)}>
                  {otherLocale === "kk" ? "Қазақ тілі" : "Русский язык"}
                </MenuLink>
                <button role="menuitem" onClick={logout} className="tap-target w-full text-left rounded-lg px-3 text-danger hover:bg-background">
                  {t("logout")}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}

function MenuLink({ href, onClick, children }: { href: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <Link href={href} role="menuitem" onClick={onClick} className="tap-target flex items-center rounded-lg px-3 hover:bg-background">
      {children}
    </Link>
  );
}
