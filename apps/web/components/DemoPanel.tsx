"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type DemoState = { time_offset_days: number; today: string };

/**
 * Демо-панель куратора (раздел 15.2): текущая дата приложения, сдвиг на 1, 7,
 * 30 дней и сброс. Видна только при DEMO_MODE (иначе API отвечает 403).
 */
export function DemoPanel() {
  const [state, setState] = useState<DemoState | null>(null);
  const [open, setOpen] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<DemoState>("/demo/state").then(setState).catch(() => setState(null));
  }, []);

  if (!state) return null;

  async function shift(days: number) {
    setBusy(true);
    try {
      await api.post("/demo/time-shift", { offset_days: state!.time_offset_days + days });
      window.location.reload();
    } finally {
      setBusy(false);
    }
  }

  async function reset() {
    setBusy(true);
    try {
      await api.post("/demo/reset");
      window.location.reload();
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 z-50 tap-target rounded-full border border-border bg-card px-4 py-2 text-xs shadow"
      >
        Демо · {state.today}
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 left-4 sm:left-auto z-50 rounded-xl border border-border bg-card p-3 text-sm shadow-lg sm:w-80">
      <div className="flex items-center justify-between mb-2">
        <p className="font-medium">Демо-панель</p>
        <button onClick={() => setOpen(false)} className="tap-target text-muted px-2" aria-label="Свернуть">
          ×
        </button>
      </div>
      <p className="mb-2">
        Дата: <span className="font-medium">{state.today}</span>
        {state.time_offset_days !== 0 && <span className="text-muted"> (сдвиг {state.time_offset_days} дн.)</span>}
      </p>
      <div className="grid grid-cols-4 gap-2">
        {[1, 7, 30].map((d) => (
          <button key={d} disabled={busy} onClick={() => shift(d)} className="tap-target rounded-lg border border-border py-2 disabled:opacity-50">
            +{d}
          </button>
        ))}
        <button disabled={busy} onClick={reset} className="tap-target rounded-lg border border-border py-2 disabled:opacity-50">
          Сброс
        </button>
      </div>
      <a href="/api/dev/mail" target="_blank" className="block text-xs text-muted underline mt-2">
        /dev/mail
      </a>
    </div>
  );
}
