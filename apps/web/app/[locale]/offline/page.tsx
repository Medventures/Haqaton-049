import { getTranslations } from "next-intl/server";

export default async function OfflinePage() {
  const t = await getTranslations("common");
  return (
    <main className="min-h-dvh flex items-center justify-center px-6 text-center">
      <div>
        <h1 className="text-2xl font-medium mb-2">{t("offline", { date: "" })}</h1>
        <p className="text-muted text-sm">AqylRoute</p>
      </div>
    </main>
  );
}
