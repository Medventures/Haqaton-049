/**
 * Смысловые разделы интервью для интерфейса. Порядок вопросов задаёт сервер
 * (раздел 11.1: сначала обязательные Q01–Q04, Q14, Q16, в конце Q17–Q18),
 * поэтому разделы идут в том же порядке.
 */
export const BLOCK_ORDER = ["child", "docs", "health", "education", "social", "priority"] as const;
export type BlockKey = (typeof BLOCK_ORDER)[number];

const BLOCK_BY_QUESTION: Record<string, BlockKey> = {
  Q01: "child",
  Q02: "child",
  Q03: "child",
  Q04: "child",
  Q14: "docs",
  Q15: "docs",
  Q16: "health",
  Q05: "education",
  Q06: "education",
  Q07: "education",
  Q08: "education",
  Q09: "education",
  Q13: "education",
  Q10: "social",
  Q11: "social",
  Q12: "social",
  Q17: "priority",
  Q18: "priority",
};

export function blockOf(questionId: string): BlockKey {
  return BLOCK_BY_QUESTION[questionId] ?? "priority";
}
