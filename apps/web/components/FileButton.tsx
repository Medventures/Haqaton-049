/** Кнопка-карточка для скачивания PDF: иконка, название и пояснение. */
export function DownloadButton({ href, title, hint }: { href: string; title: string; hint?: string }) {
  return (
    <a
      href={href}
      download
      className="tap-target flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 hover:border-medicine/60"
    >
      <span className="flex items-center justify-center w-10 h-10 rounded-lg bg-medicine/15 text-medicine shrink-0" aria-hidden>
        <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 4v11m0 0l-4-4m4 4l4-4M5 19h14" />
        </svg>
      </span>
      <span className="min-w-0">
        <span className="block font-medium">{title}</span>
        {hint && <span className="block text-xs text-muted">{hint}</span>}
      </span>
    </a>
  );
}
