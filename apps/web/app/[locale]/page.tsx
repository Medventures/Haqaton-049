import { getTranslations } from "next-intl/server";
import Link from "next/link";

export default async function LandingPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations("landing");

  return (
    <main className="min-h-dvh flex flex-col items-center justify-center gap-8 px-6 text-center">
      <div className="max-w-2xl">
        <h1 className="text-3xl md:text-4xl font-medium tracking-tight mb-4">{t("title")}</h1>
        <p className="text-muted text-lg">{t("subtitle")}</p>
      </div>
      <div className="flex flex-wrap gap-3 justify-center">
        <Link
          href={`/${locale}/login?role=parent`}
          className="tap-target px-5 py-3 rounded-lg bg-medicine text-background font-medium"
        >
          {t("ctaParent")}
        </Link>
        <Link
          href={`/${locale}/login?role=curator`}
          className="tap-target px-5 py-3 rounded-lg border border-border"
        >
          {t("ctaCurator")}
        </Link>
        <Link href={`/${locale}/login`} className="tap-target px-5 py-3 rounded-lg border border-border">
          {t("login")}
        </Link>
      </div>
    </main>
  );
}
