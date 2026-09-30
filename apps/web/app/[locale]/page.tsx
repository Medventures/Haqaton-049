import { getTranslations } from "next-intl/server";
import Link from "next/link";
import { EducationIcon, MedicineIcon, SocialIcon } from "@/components/icons";

export default async function LandingPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations("landing");
  const how = t.raw("how") as { t: string; d: string }[];
  const icons = [MedicineIcon, EducationIcon, SocialIcon];
  const colors = ["text-medicine", "text-education", "text-social"];

  return (
    <main className="min-h-dvh flex flex-col">
      <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 py-12">
        <div className="flex gap-3 mb-8" aria-hidden>
          {icons.map((Icon, i) => (
            <span key={i} className={`flex items-center justify-center w-12 h-12 rounded-2xl border border-border bg-card ${colors[i]}`}>
              <Icon className="w-6 h-6" />
            </span>
          ))}
        </div>
        <div className="max-w-2xl text-center">
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4">{t("title")}</h1>
          <p className="text-muted text-lg">{t("subtitle")}</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 mt-8 w-full max-w-md sm:max-w-none sm:w-auto">
          <Link href={`/${locale}/login?role=parent`} className="tap-target flex items-center justify-center px-6 py-3 rounded-xl bg-medicine text-background font-medium">
            {t("ctaParent")}
          </Link>
          <Link href={`/${locale}/login?role=curator`} className="tap-target flex items-center justify-center px-6 py-3 rounded-xl border border-border bg-card">
            {t("ctaCurator")}
          </Link>
        </div>

        <section className="w-full max-w-3xl mt-14">
          <h2 className="text-lg font-medium text-center mb-4">{t("howTitle")}</h2>
          <ol className="grid sm:grid-cols-3 gap-3">
            {how.map((step, i) => (
              <li key={i} className="rounded-xl border border-border bg-card px-4 py-4">
                <span className="flex items-center justify-center w-8 h-8 rounded-full border border-border text-sm mb-3">{i + 1}</span>
                <p className="font-medium mb-1">{step.t}</p>
                <p className="text-sm text-muted">{step.d}</p>
              </li>
            ))}
          </ol>
        </section>

        <Link href={`/${locale}/faq`} className="tap-target inline-flex items-center mt-8 text-sm underline text-muted">
          {t("faqLink")}
        </Link>
      </div>
    </main>
  );
}
