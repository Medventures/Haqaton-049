"""Режим заглушки (раздел 12 SPEC.md): "Если OPENAI_API_KEY пуст, модуль
работает в режиме заглушки: вызов 1 возвращает первый допустимый вопрос,
вызов 2 пустой результат, вызов 3 шаблон из справочника, вызов 4 пустые
поля." Тесты всегда используют заглушку или мок.
"""
PRIORITY_RANK = {"mandatory": 0, "high": 1, "medium": 2, "low": 3}


def choose_next_question(allowed: list[dict]) -> str | None:
    if not allowed:
        return None
    non_filler = [q for q in allowed if q["id"] not in ("Q17", "Q18")]
    pool = non_filler if non_filler else allowed
    ordered = sorted(pool, key=lambda q: (PRIORITY_RANK.get(q["priority"], 9), q["id"]))
    return ordered[0]["id"]


def parse_q17(masked_text: str) -> dict:
    return {"red_flags": [], "priority_focus": None}


def explain_step(service: dict, lang: str) -> str:
    return service[f"explanation_template_{lang}"]


def parse_document(masked_text: str) -> dict:
    return {"doc_type": None, "issued_at": None, "valid_until": None, "issuer": None}
