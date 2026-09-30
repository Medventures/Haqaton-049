"use client";

import { useEffect, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { AppHeader } from "@/components/AppHeader";
import { formatDateTime } from "@/lib/parent";

/**
 * Раздел 16.4-16.5: регистрация service worker, своя кнопка установки
 * (+ инструкция для iOS), баннер "доступно обновление", очистка
 * приватного кеша при выходе, баннер офлайн (раздел 16.3).
 */
export function AppChrome({ hideInstall = false }: { hideInstall?: boolean }) {
  const t = useTranslations("common");
  const locale = useLocale();
  const [online, setOnline] = useState(true);
  const [installPrompt, setInstallPrompt] = useState<Event | null>(null);
  const [isIOS, setIsIOS] = useState(false);
  const [updateReady, setUpdateReady] = useState(false);
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(null);

  useEffect(() => {
    setOnline(navigator.onLine);
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);

    setIsIOS(/iphone|ipad|ipod/i.test(navigator.userAgent));

    const onBeforeInstall = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e);
    };
    window.addEventListener("beforeinstallprompt", onBeforeInstall);

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").then((reg) => {
        if (reg.waiting) setWaitingWorker(reg.waiting);
        reg.addEventListener("updatefound", () => {
          const nw = reg.installing;
          nw?.addEventListener("statechange", () => {
            if (nw.state === "installed" && navigator.serviceWorker.controller) {
              setWaitingWorker(nw);
              setUpdateReady(true);
            }
          });
        });
      });
    }

    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
      window.removeEventListener("beforeinstallprompt", onBeforeInstall);
    };
  }, []);

  async function install() {
    if (!installPrompt) return;
    // @ts-expect-error BeforeInstallPromptEvent не типизирован в lib.dom
    installPrompt.prompt();
    setInstallPrompt(null);
  }

  function reloadForUpdate() {
    waitingWorker?.postMessage({ type: "SKIP_WAITING" });
    window.location.reload();
  }

  return (
    <>
      {!online && (
        <div className="bg-social/20 text-social text-sm text-center py-2 px-4">
          {t("offline", { date: formatDateTime(new Date().toISOString(), locale) })}
        </div>
      )}
      {updateReady && (
        <div className="bg-medicine/20 text-sm text-center py-2 px-4 flex items-center justify-center gap-3">
          <span>Доступно обновление</span>
          <button onClick={reloadForUpdate} className="underline">
            Обновить
          </button>
        </div>
      )}
      {!hideInstall && (installPrompt || isIOS) && (
        <div className="text-xs text-center py-1.5 px-4 text-muted border-b border-border">
          {installPrompt ? (
            <button onClick={install} className="underline">
              Установить приложение
            </button>
          ) : (
            "Поделиться → На экран «Домой»"
          )}
        </div>
      )}
      <AppHeader />
    </>
  );
}
