/**
 * Раздел 15.3: никаких готовых наборов иконок, только свои SVG из
 * простых геометрических форм. Ведомства и статусы различаются формой,
 * а не только цветом.
 */
type IconProps = { className?: string };

export function MedicineIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="10" y="3" width="4" height="18" rx="1" />
      <rect x="3" y="10" width="18" height="4" rx="1" />
    </svg>
  );
}

export function EducationIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 4 2 9l10 5 10-5-10-5Z" strokeLinejoin="round" />
      <path d="M6 12v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5" strokeLinejoin="round" />
    </svg>
  );
}

export function SocialIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="9" cy="8" r="3" />
      <circle cx="17" cy="9" r="2.4" />
      <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" strokeLinecap="round" />
      <path d="M15.5 14.3c2.5.4 4.5 2.4 4.5 5.7" strokeLinecap="round" />
    </svg>
  );
}

export const AGENCY_ICON = {
  medicine: MedicineIcon,
  education: EducationIcon,
  social: SocialIcon,
};

export function StatusDot({ status, className }: { status: string; className?: string }) {
  const shapes: Record<string, string> = {
    not_started: "circle",
    blocked: "square",
    in_progress: "triangle",
    done_by_parent: "diamond",
    done: "check",
    overdue: "cross",
  };
  const shape = shapes[status] ?? "circle";
  if (shape === "check") {
    return (
      <svg viewBox="0 0 16 16" className={className} fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 8.5 6.5 12 13 4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (shape === "cross") {
    return (
      <svg viewBox="0 0 16 16" className={className} fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 4l8 8M12 4l-8 8" strokeLinecap="round" />
      </svg>
    );
  }
  if (shape === "square") {
    return (
      <svg viewBox="0 0 16 16" className={className}>
        <rect x="3" y="3" width="10" height="10" rx="1.5" fill="currentColor" />
      </svg>
    );
  }
  if (shape === "triangle") {
    return (
      <svg viewBox="0 0 16 16" className={className}>
        <path d="M8 2 14 13H2Z" fill="currentColor" />
      </svg>
    );
  }
  if (shape === "diamond") {
    return (
      <svg viewBox="0 0 16 16" className={className}>
        <path d="M8 2 14 8 8 14 2 8Z" fill="currentColor" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 16 16" className={className}>
      <circle cx="8" cy="8" r="5.5" fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}
