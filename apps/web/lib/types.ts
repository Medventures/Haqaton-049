export type StepDocument = { doc_type: string; kind: string; in_wallet: boolean; note: string | null };

export type Step = {
  step_id: string;
  service_id: string;
  title_ru: string;
  title_kk: string;
  agency: "medicine" | "education" | "social";
  responsible: "parent" | "education_org" | "curator";
  priority: "critical" | "high" | "medium" | "low";
  depends_on: string[];
  start_date: string | null;
  deadline: string | null;
  original_deadline: string | null;
  documents: StepDocument[];
  status: "not_started" | "blocked" | "in_progress" | "done_by_parent" | "done" | "overdue";
  explanation_ru: string | null;
  explanation_kk: string | null;
  rule_id: string | null;
  source_ids: string[];
  provider_ids: string[];
  added_by: "engine" | "curator";
  needs_clarification: boolean;
  deadline_compressed: boolean;
  escalation_level: number;
  status_history: unknown[];
};

export type PlanJson = {
  case_id: string;
  family_id: string;
  version: number;
  status: "draft" | "approved" | "archived";
  computed_at: string;
  steps: Step[];
  approved_by: number | null;
  approved_at: string | null;
};

export type DocumentTypeRef = {
  doc_type: string;
  title_ru: string;
  title_kk: string;
  issuer_ru: string | null;
  issuer_kk: string | null;
  validity_ru: string | null;
  validity_kk: string | null;
};

export type ProviderRef = {
  provider_id: string;
  name_ru: string;
  name_kk: string;
  address_ru: string | null;
  address_kk: string | null;
  phone: string | null;
  hours_ru: string | null;
  hours_kk: string | null;
  booking_methods: string[] | null;
};

export type Reference = {
  today: string;
  document_types: Record<string, DocumentTypeRef>;
  providers: Record<string, ProviderRef>;
};
