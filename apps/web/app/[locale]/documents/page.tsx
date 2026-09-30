"use client";

import { useEffect, useState, type ChangeEvent } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/lib/api";

type Doc = {
  id: number;
  doc_type: string;
  valid_until: string | null;
  confirmed_by_parent: boolean;
  verified_by: number | null;
};

export default function DocumentsPage() {
  const t = useTranslations("documents");
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

  const missing = docs.filter((d) => !d.valid_until && !d.confirmed_by_parent);

  return (
    <main className="min-h-dvh px-6 py-10 max-w-xl mx-auto w-full">
      <h1 className="text-2xl font-medium mb-6">{t("title")}</h1>

      <label className="tap-target block text-center rounded-lg border border-dashed border-border px-4 py-4 mb-6 cursor-pointer">
        {uploading ? "…" : t("upload")}
        <input type="file" className="hidden" onChange={onUpload} disabled={uploading} accept="application/pdf,image/*" />
      </label>

      {missing.length > 0 && (
        <section className="mb-6">
          <h2 className="font-medium mb-2 text-danger">{t("missing")}</h2>
        </section>
      )}

      <section>
        <h2 className="font-medium mb-2">{t("list")}</h2>
        <div className="flex flex-col gap-2">
          {docs.map((d) => (
            <div key={d.id} className="flex items-center justify-between rounded-lg border border-border bg-card px-3 py-2 text-sm">
              <span>{d.doc_type}</span>
              <span className="text-muted">{d.valid_until ?? "—"}</span>
              <span className={d.verified_by ? "text-education" : "text-muted"}>{d.verified_by ? "✓" : ""}</span>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
