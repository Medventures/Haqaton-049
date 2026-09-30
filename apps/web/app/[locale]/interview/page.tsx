"use client";

import { useEffect, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { AppChrome } from "@/components/AppChrome";
import { BLOCK_ORDER, blockOf, type BlockKey } from "@/lib/interviewBlocks";

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
type Screen = { kind: "intro" } | { kind: "question" } | { kind: "section"; done: BlockKey; next: BlockKey };

/**
 * Интервью (раздел 15.1): один вопрос на экран. Порядок вопросов задаёт
 * сервер (раздел 11.1), а сайт группирует их в смысловые разделы и между
 * разделами показывает отдельный экран с кнопками «Далее» и «Назад».
 */
export default function InterviewPage() {
  const t = useTranslations("interview");
  const tUi = useTranslations("interviewUi");
  const tB = useTranslations("blocks");
  const tCommon = useTranslations("common");
  const locale = useLocale() as "ru" | "kk";
  const router = useRouter();
  const [state, setState] = useState<InterviewState | null>(null);
  const [screen, setScreen] = useState<Screen>({ kind: "question" });
  const [answered, setAnswered] = useState(0);
  const [visited, setVisited] = useState<BlockKey[]>([]);
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
        // Первый вопрос всегда Q01: значит интервью только начинается.
        if (s.question?.id === "Q01") setScreen({ kind: "intro" });
      })
      .catch((e) => setError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function submit() {
    if (!state?.question) return;
    setBusy(true);
    setError(null);
    const current = blockOf(state.question.id);
    try {
      const next = await api.post<InterviewState>("/interview/answer", {
        question_id: state.question.id,
        value,
      });
      setAnswered((n) => n + 1);
      setValue(undefined);
      setVisited((v) => (v.includes(current) ? v : [...v, current]));
      if (next.done) {
        await api.post("/interview/finish");
        router.push(`/${locale}/plan?justFinished=1`);
        return;
      }
      setState(next);
      const upcoming = next.question ? blockOf(next.question.id) : current;
      setScreen(upcoming !== current ? { kind: "section", done: current, next: upcoming } : { kind: "question" });
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function back() {
    setBusy(true);
    setError(null);
    try {
      const prev = await api.post<InterviewState>("/interview/back");
      setState(prev);
      setValue(undefined);
      setAnswered((n) => Math.max(0, n - 1));
      setScreen({ kind: "question" });
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  if (error && !state) return <Centered>{error}</Centered>;
  if (!state) return <Centered>…</Centered>;
  if (state.done || !state.question) return <Centered>{t("finishBody")}</Centered>;

  const q = state.question;
  const block = blockOf(q.id);
  const blockIdx = BLOCK_ORDER.indexOf(block);
  const canSubmit = value !== undefined && value !== "" && !(Array.isArray(value) && value.length === 0);

  if (screen.kind === "intro") {
    return (
      <Shell>
        <div className="flex-1 flex flex-col justify-center">
          <h1 className="text-3xl font-semibold mb-3">{tUi("introTitle")}</h1>
          <p className="text-muted mb-8">{tUi("introBody")}</p>
          <ol className="flex flex-col gap-2">
            {BLOCK_ORDER.map((b, i) => (
              <li key={b} className="flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3">
                <span className="flex items-center justify-center w-8 h-8 rounded-full border border-border text-sm shrink-0">{i + 1}</span>
                <span>
                  <span className="block font-medium">{tB(`${b}.title`)}</span>
                  <span className="block text-sm text-muted">{tB(`${b}.desc`)}</span>
                </span>
              </li>
            ))}
          </ol>
        </div>
        <ActionBar>
          <button onClick={() => setScreen({ kind: "question" })} className="tap-target flex-1 rounded-xl bg-medicine text-background font-medium py-3">
            {tUi("start")}
          </button>
        </ActionBar>
      </Shell>
    );
  }

  if (screen.kind === "section") {
    const nextIdx = BLOCK_ORDER.indexOf(screen.next);
    return (
      <Shell>
        <Stepper current={screen.next} visited={visited} />
        <div className="flex-1 flex flex-col justify-center text-center items-center">
          <span className="flex items-center justify-center w-16 h-16 rounded-full bg-education/15 text-education mb-5" aria-hidden>
            <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M5 12l5 5 9-10" />
            </svg>
          </span>
          <p className="text-lg font-medium mb-1">{tUi("sectionDone", { name: tB(`${screen.done}.title`) })}</p>
          <p className="text-sm text-muted mb-8">{tUi("answered", { n: answered })}</p>
          <div className="w-full rounded-xl border border-border bg-card px-5 py-4 text-left">
            <p className="text-xs text-muted mb-1">
              {tUi("nextSection")} · {tUi("sectionOf", { n: nextIdx + 1, total: BLOCK_ORDER.length })}
            </p>
            <p className="text-xl font-semibold">{tB(`${screen.next}.title`)}</p>
            <p className="text-sm text-muted">{tB(`${screen.next}.desc`)}</p>
          </div>
        </div>
        {error && <p className="text-danger text-sm mb-2">{error}</p>}
        <ActionBar>
          <button onClick={back} disabled={busy} className="tap-target rounded-xl border border-border px-5 py-3 disabled:opacity-50">
            ← {tUi("back")}
          </button>
          <button onClick={() => setScreen({ kind: "question" })} className="tap-target flex-1 rounded-xl bg-medicine text-background font-medium py-3">
            {tUi("continue")} →
          </button>
        </ActionBar>
      </Shell>
    );
  }

  return (
    <Shell>
      <Stepper current={block} visited={visited} />
      <p className="text-xs text-muted mb-1">
        {tUi("sectionOf", { n: blockIdx + 1, total: BLOCK_ORDER.length })} · {tB(`${block}.title`)}
      </p>
      <p className="text-sm text-muted mb-4">{t("progress", { current: answered + 1, min: 8, max: 12 })}</p>
      <h1 className="text-2xl font-semibold mb-4">{q[`text_${locale}`]}</h1>
      <div className="rounded-xl border border-border bg-card px-4 py-3 text-sm mb-6">
        <span className="font-medium">{t("why")}:</span> <span className="text-muted">{q[`hint_${locale}`]}</span>
      </div>

      <QuestionInput question={q} locale={locale} value={value} onChange={setValue} />

      {error && <p className="text-danger text-sm mt-4">{error}</p>}

      <ActionBar>
        {answered > 0 && (
          <button onClick={back} disabled={busy} className="tap-target rounded-xl border border-border px-5 py-3 disabled:opacity-50">
            ← {tUi("back")}
          </button>
        )}
        <button
          onClick={submit}
          disabled={busy || !canSubmit}
          className="tap-target flex-1 rounded-xl bg-medicine text-background font-medium py-3 disabled:opacity-50"
        >
          {tUi("continue")} →
        </button>
      </ActionBar>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-dvh flex flex-col">
      <AppChrome hideInstall />
      <div className="flex-1 flex flex-col max-w-xl mx-auto w-full px-4 sm:px-6 pt-6">{children}</div>
    </main>
  );
}

/** Кнопки прижаты к низу экрана, чтобы на телефоне до них было удобно дотянуться. */
function ActionBar({ children }: { children: React.ReactNode }) {
  return (
    <>
      <div aria-hidden className="h-24" />
      <div className="fixed bottom-0 inset-x-0 z-30 border-t border-border bg-background/95 backdrop-blur pb-[env(safe-area-inset-bottom)]">
        <div className="max-w-xl mx-auto flex gap-3 px-4 py-3">{children}</div>
      </div>
    </>
  );
}

function Stepper({ current, visited }: { current: BlockKey; visited: BlockKey[] }) {
  const tB = useTranslations("blocks");
  return (
    <ol className="flex gap-1.5 mb-5" aria-label={tB(`${current}.title`)}>
      {BLOCK_ORDER.map((b) => (
        <li
          key={b}
          title={tB(`${b}.title`)}
          aria-current={b === current ? "step" : undefined}
          className={`h-1.5 flex-1 rounded-full ${
            b === current ? "bg-medicine" : visited.includes(b) ? "bg-education" : "bg-border"
          }`}
        />
      ))}
    </ol>
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
        className="tap-target rounded-xl border border-border bg-card px-4 py-3 text-lg w-32"
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
        className="rounded-xl border border-border bg-card px-4 py-3"
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
        <OptionRow key={o.code} multi selected={arr.includes(o.code)} label={o[`label_${locale}`]} onClick={() => toggle(o.code)} />
      ))}
    </div>
  );
}

function OptionRow({
  selected,
  label,
  onClick,
  multi = false,
}: {
  selected: boolean;
  label: string;
  onClick: () => void;
  multi?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`tap-target flex items-center gap-3 text-left rounded-xl border px-4 py-3 ${
        selected ? "border-medicine bg-medicine/10" : "border-border bg-card"
      }`}
    >
      <span
        aria-hidden
        className={`flex items-center justify-center w-5 h-5 shrink-0 border-2 ${multi ? "rounded-md" : "rounded-full"} ${
          selected ? "border-medicine bg-medicine text-background" : "border-muted"
        }`}
      >
        {selected && (
          <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="3.5">
            <path d="M5 12l5 5 9-10" />
          </svg>
        )}
      </span>
      {label}
    </button>
  );
}
