"""Единая точка входа в LLM-модуль (раздел 12 SPEC.md).

Реальная интеграция с OpenAI (маскирование -> API -> фильтр формулировок,
раздел 12.2-12.3) — предмет этапа 2 (docs/DECISIONS.md). Пока
`OPENAI_API_KEY` пуст (по умолчанию в этом окружении), модуль всегда
работает в режиме заглушки, что и требуется для детерминированных тестов
этапа 1 (раздел 12: "Тесты всегда используют заглушку или мок").
"""
from app.config import get_settings
from app.modules.llm import masking, stub


class LlmNotConfiguredError(NotImplementedError):
    pass


def _stub_mode() -> bool:
    return not get_settings().openai_api_key


def choose_next_question(answers: list[dict], allowed: list[dict]) -> str | None:
    """Вызов 1 (раздел 12.2): выбор следующего вопроса из allowed."""
    if _stub_mode():
        return stub.choose_next_question(allowed)
    raise LlmNotConfiguredError(
        "Реальный вызов OpenAI для выбора вопроса — раздел 12, этап 2"
    )


def parse_q17(text: str, child_name: str | None = None, parent_name: str | None = None) -> dict:
    """Вызов 2 (раздел 12.2): разбор свободного ответа на Q17."""
    masked = masking.mask_text(text, child_name=child_name, parent_name=parent_name)
    if _stub_mode():
        return stub.parse_q17(masked)
    raise LlmNotConfiguredError("Реальный вызов OpenAI для разбора Q17 — раздел 12, этап 2")


def explain_step(service: dict, lang: str, needs_clarification: bool = False, deadline_compressed: bool = False) -> str:
    """Вызов 3 (раздел 12.2): объяснение шага. В режиме заглушки — шаблон
    из справочника (`explanation_template_ru`/`explanation_template_kk`).
    """
    if _stub_mode():
        return stub.explain_step(service, lang)
    raise LlmNotConfiguredError("Реальный вызов OpenAI для объяснения шага — раздел 12, этап 2")
