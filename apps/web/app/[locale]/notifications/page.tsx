"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/lib/api";

type Notif = { id: number; type: string; payload: Record<string, unknown>; created_at: string; read_at: string | null };

export default function NotificationsPage() {
  const t = useTranslations("notifications");
  const [items, setItems] = useState<Notif[]>([]);

  async function reload() {
    setItems(await api.get<Notif[]>("/notifications"));
  }

  useEffect(() => {
    reload();
  }, []);

  async function markAllRead() {
    const unread = items.filter((n) => !n.read_at).map((n) => n.id);
    if (!unread.length) return;
    await api.post("/notifications/read", { ids: unread });
    await reload();
  }

  return (
    <main className="min-h-dvh px-6 py-10 max-w-xl mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-medium">{t("title")}</h1>
        <button onClick={markAllRead} className="text-sm underline">
          {t("markRead")}
        </button>
      </div>
      <div className="flex flex-col gap-2">
        {items.length === 0 && <p className="text-muted">{t("empty")}</p>}
        {items.map((n) => (
          <div
            key={n.id}
            className={`rounded-lg border border-border px-4 py-3 text-sm ${n.read_at ? "opacity-60" : "bg-card"}`}
          >
            <p className="font-medium">{n.type}</p>
            <p className="text-muted text-xs mt-1">{n.created_at}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
