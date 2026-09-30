"use client";

import { useEffect, useState, type ChangeEvent } from "react";
import { useLocale, useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { AppChrome } from "@/components/AppChrome";
import { ParentNav } from "@/components/ParentNav";
import { isOpen, useParentData } from "@/lib/parent";

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
    try {
      const form = new FormData();
      form.append("file", file);
      await fetch("/api/documents", { method: "POST", body: form, credentials: "include" });
      await reload(familyId);
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
      <h1 className="text-2xl font-medium pt-4 mb-6">{t("title")}</h1>

      <label className="tap-target block text-center rounded-lg border border-dashed border-border px-4 py-4 mb-6 cursor-pointer">
        {uploading ? "…" : t("upload")}
        <input type="file" className="hidden" onChange={onUpload} disabled={uploading} accept="application/pdf,image/*" />
      </label>

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
