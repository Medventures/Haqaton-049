"use client";

import { useEffect, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { AppChrome } from "@/components/AppChrome";

type Option = { code: string; label_ru: string; label_kk: string };
type Question = {
  id: string;
  text_ru: string;
  text_kk: string;
  hint_ru: string;
  hint_kk: string;
  answer_type: "number" | "single" | "multi" | "date_or_unknown" | "text";
  options: Option[];
  min?: number;
  max?: number;
  max_length?: number;
};

type InterviewState = { done: boolean; question?: Question };

export default function InterviewPage() {
  const t = useTranslations("interview");
  const tCommon = useTranslations("common");
  const locale = useLocale() as "ru" | "kk";
  const router = useRouter();
  const [state, setState] = useState<InterviewState | null>(null);
  const [answered, setAnswered] = useState(0);
  const [value, setValue] = useState<unknown>(undefined);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!navigator.onLine) {
      setError(tCommon("needsInternet"));
      return;
    }
    api
      .post<InterviewState>("/interview/start")
      .then((s) => {
        setState(s);
        setValue(undefined);
      })
      .catch((e) => setError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function submit() {
    if (!state?.question) return;
    setBusy(true);
    setError(null);
    try {
      const next = await api.post<InterviewState>("/interview/answer", {
        question_id: state.question.id,
        value,
      });
      setAnswered((n) => n + 1);
      setValue(undefined);
      if (next.done) {
        await api.post("/interview/finish");
        router.push(`/${locale}/plan?justFinished=1`);
        return;
      }
      setState(next);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function back() {
    setBusy(true);
    try {
      const prev = await api.post<InterviewState>("/interview/back");
      setState(prev);
      setValue(undefined);
      setAnswered((n) => Math.max(0, n - 1));
    } finally {
      setBusy(false);
    }
  }

  if (error) return <Centered>{error}</Centered>;
  if (!state) return <Centered>…</Centered>;
  if (state.done || !state.question) return <Centered>{t("finishBody")}</Centered>;

  const q = state.question;
  const canSubmit = value !== undefined && value !== "" && !(Array.isArray(value) && value.length === 0);

  return (
    <main className="min-h-dvh flex flex-col max-w-xl mx-auto w-full">
      <AppChrome hideInstall />
      <div className="flex-1 flex flex-col px-6 py-10">
      <p className="text-sm text-muted mb-2">{t("progress", { current: answered + 1, min: 8, max: 12 })}</p>
      <h1 className="text-2xl font-medium mb-3">{q[`text_${locale}`]}</h1>
      <p className="text-sm text-muted mb-6">
        <span className="font-medium">{t("why")}:</span> {q[`hint_${locale}`]}
      </p>

      <QuestionInput question={q} locale={locale} value={value} onChange={setValue} />

      {error && <p className="text-danger text-sm mt-4">{error}</p>}

      <div className="mt-8 flex gap-3">
        {answered > 0 && (
          <button onClick={back} disabled={busy} className="tap-target px-4 py-2 rounded-lg border border-border">
            ←
          </button>
        )}
        <button
          onClick={submit}
          disabled={busy || !canSubmit}
          className="tap-target flex-1 rounded-lg bg-medicine text-background font-medium py-2 disabled:opacity-50"
        >
          {t("submit")}
        </button>
      </div>
      </div>
    </main>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return <main className="min-h-dvh flex items-center justify-center px-6 text-center">{children}</main>;
}

function QuestionInput({
  question,
  locale,
  value,
  onChange,
}: {
  question: Question;
  locale: "ru" | "kk";
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  if (question.answer_type === "number") {
    return (
      <input
        type="number"
        min={question.min ?? 0}
        max={question.max ?? 17}
        value={(value as number) ?? ""}
        onChange={(e) => onChange(e.target.value === "" ? undefined : Number(e.target.value))}
        className="tap-target rounded-lg border border-border bg-card px-4 py-3 text-lg w-32"
      />
    );
  }

  if (question.answer_type === "text") {
    return (
      <textarea
        maxLength={question.max_length ?? 500}
        value={(value as string) ?? ""}
        onChange={(e) => onChange(e.target.value)}
        rows={5}
        className="rounded-lg border border-border bg-card px-4 py-3"
      />
    );
  }

  if (question.answer_type === "date_or_unknown") {
    const isUnknown = value === "unknown";
    return (
      <div className="flex flex-col gap-3">
        <input
          type="date"
          disabled={isUnknown}
          value={isUnknown ? "" : (value as string) ?? ""}
          onChange={(e) => onChange(e.target.value)}
          className="tap-target rounded-lg border border-border bg-card px-4 py-3 disabled:opacity-40"
        />
        <OptionRow
          selected={isUnknown}
          label={question.options[0]?.[`label_${locale}`] ?? "unknown"}
          onClick={() => onChange("unknown")}
        />
      </div>
    );
  }

  if (question.answer_type === "single") {
    return (
      <div className="flex flex-col gap-2">
        {question.options.map((o) => (
          <OptionRow key={o.code} selected={value === o.code} label={o[`label_${locale}`]} onClick={() => onChange(o.code)} />
        ))}
      </div>
    );
  }

  // multi
  const arr = (value as string[]) ?? [];
  function toggle(code: string) {
    if (code === "none") {
      onChange(arr.includes("none") ? [] : ["none"]);
      return;
    }
    const withoutNone = arr.filter((c) => c !== "none");
    onChange(withoutNone.includes(code) ? withoutNone.filter((c) => c !== code) : [...withoutNone, code]);
  }
  return (
    <div className="flex flex-col gap-2">
      {question.options.map((o) => (
        <OptionRow key={o.code} selected={arr.includes(o.code)} label={o[`label_${locale}`]} onClick={() => toggle(o.code)} />
      ))}
    </div>
  );
}

function OptionRow({ selected, label, onClick }: { selected: boolean; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`tap-target text-left rounded-lg border px-4 py-3 transition-colors ${
        selected ? "border-medicine bg-medicine/10" : "border-border bg-card"
      }`}
    >
      <span className="mr-2">{selected ? "●" : "○"}</span>
      {label}
    </button>
  );
}
