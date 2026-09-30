"use client";

import { useEffect, useState, type ChangeEvent } from "react";
import { useLocale, useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { AppChrome } from "@/components/AppChrome";
import { ParentNav } from "@/components/ParentNav";
import { formatDate, isOpen, useParentData } from "@/lib/parent";

type Doc = {
  id: number;
  doc_type: string;
  valid_until: string | null;
  confirmed_by_parent: boolean;
  verified_by: number | null;
};

export default function DocumentsPage() {
  const t = useTranslations("documents");
  const locale = useLocale() as "ru" | "kk";
  const { plan, reference } = useParentData();
  const [familyId, setFamilyId] = useState<number | null>(null);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<
    { ok: true; docType: string | null; validUntil: string | null; name: string } | { ok: false; needsType: boolean } | null
  >(null);
  const tPdf = useTranslations("pdf");
  const [docTypeHint, setDocTypeHint] = useState("");

  async function reload(id: number) {
    setDocs(await api.get<Doc[]>(`/documents?family=${id}`));
  }

  useEffect(() => {
    api.get<{ id: number }>("/families/me").then((f) => {
      setFamilyId(f.id);
      reload(f.id);
    });
  }, []);

  async function onUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !familyId) return;
    setUploading(true);
    setUploadResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      if (docTypeHint) form.append("doc_type_hint", docTypeHint);
      const res = await fetch("/api/documents", { method: "POST", body: form, credentials: "include" });
      if (!res.ok) {
        // 422 без подсказки: тип не распознан, просим выбрать его вручную.
        setUploadResult({ ok: false, needsType: res.status === 422 && !docTypeHint });
        return;
      }
      const doc = (await res.json()) as { doc_type: string | null; valid_until: string | null };
      setUploadResult({ ok: true, docType: doc.doc_type, validUntil: doc.valid_until, name: file.name });
      await reload(familyId);
    } catch {
      setUploadResult({ ok: false, needsType: false });
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  // «Не хватает» (раздел 15.1): обязательные документы открытых шагов, которых нет в кошельке.
  const missing = new Map<string, string[]>();
  for (const step of plan?.steps ?? []) {
    if (!isOpen(step)) continue;
    for (const d of step.documents) {
      if (d.kind !== "required" || d.in_wallet) continue;
      missing.set(d.doc_type, [...(missing.get(d.doc_type) ?? []), step[`title_${locale}`]]);
    }
  }
  const docTitle = (docType: string) => reference?.document_types[docType]?.[`title_${locale}`] ?? docType;

  return (
    <main className="min-h-dvh max-w-xl mx-auto w-full">
      <AppChrome />
      <div className="px-4 sm:px-6 pb-6">
      <h1 className="text-2xl font-semibold pt-6 mb-6">{t("title")}</h1>

      <label className="flex flex-col gap-1 mb-3 text-sm">
        <span className="text-muted">{tPdf("docType")}</span>
        <select
          value={docTypeHint}
          onChange={(e) => setDocTypeHint(e.target.value)}
          className="tap-target rounded-xl border border-border bg-card px-3 py-2"
        >
          <option value="">{tPdf("docTypeAuto")}</option>
          {Object.values(reference?.document_types ?? {}).map((d) => (
            <option key={d.doc_type} value={d.doc_type}>
              {d[`title_${locale}`]}
            </option>
          ))}
        </select>
      </label>
      <label className="tap-target flex items-center gap-3 rounded-xl border-2 border-dashed border-border bg-card px-4 py-4 mb-3 cursor-pointer hover:border-medicine/60">
        <span className="flex items-center justify-center w-10 h-10 rounded-lg bg-education/15 text-education shrink-0" aria-hidden>
          <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 16V5m0 0l-4 4m4-4l4 4M5 19h14" />
          </svg>
        </span>
        <span>
          <span className="block font-medium">{uploading ? tPdf("uploading") : tPdf("uploadTitle")}</span>
          <span className="block text-xs text-muted">{tPdf("uploadHint")}</span>
        </span>
        <input type="file" className="sr-only" onChange={onUpload} disabled={uploading} accept="application/pdf,image/*" />
      </label>
      <div aria-live="polite" className="mb-6 text-sm">
        {uploadResult?.ok === true && (
          <p className="rounded-lg border border-education/50 px-3 py-2">
            ✓ {tPdf("uploadOk", { title: uploadResult.docType ? docTitle(uploadResult.docType) : uploadResult.name })}
            {uploadResult.validUntil && <>, {tPdf("validUntil", { date: formatDate(uploadResult.validUntil, locale, true) })}</>}
          </p>
        )}
        {uploadResult?.ok === false && (
          <p className="rounded-lg border border-danger/50 text-danger px-3 py-2">
            {uploadResult.needsType ? tPdf("needsType") : tPdf("uploadError")}
          </p>
        )}
      </div>

      {missing.size > 0 && (
        <section className="mb-6">
          <h2 className="font-medium mb-2 text-danger">{t("missing")}</h2>
          <div className="flex flex-col gap-2">
            {[...missing].map(([docType, stepTitles]) => (
              <div key={docType} className="rounded-lg border border-danger/50 bg-card px-3 py-2 text-sm">
                <p className="font-medium">{docTitle(docType)}</p>
                <p className="text-xs text-muted">{stepTitles.join(", ")}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="font-medium mb-2">{t("list")}</h2>
        <div className="flex flex-col gap-2">
          {docs.map((d) => (
            <div key={d.id} className="flex items-center justify-between rounded-lg border border-border bg-card px-3 py-2 text-sm">
              <span>{docTitle(d.doc_type)}</span>
              <span className="text-muted">{d.valid_until ?? "—"}</span>
              <span className={d.verified_by ? "text-education" : "text-muted"}>{d.verified_by ? "✓" : ""}</span>
            </div>
          ))}
        </div>
      </section>
      </div>
      <ParentNav current="documents" />
    </main>
  );
}
