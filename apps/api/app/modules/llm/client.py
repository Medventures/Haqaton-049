"""Единая точка входа в LLM-модуль (раздел 12 SPEC.md).

Настройки вызова: модель из `OPENAI_MODEL`, `temperature: 0`, `seed: 42`,
structured outputs (`json_schema`, `strict: true`). Пока `OPENAI_API_KEY`
пуст (по умолчанию в этом окружении), модуль всегда работает в режиме
заглушки — требование раздела 12 ("Тесты всегда используют заглушку или
мок"). Реальный путь ниже не покрыт тестами (нет ключа в CI/этом
окружении), см. docs/DECISIONS.md.
"""
from app.config import get_settings
from app.modules.llm import masking, stub
from app.modules.llm.filter import check_text

AGE_GROUPS = [(2, "0-2"), (6, "3-6"), (17, "7-17")]


def age_group(age: int | None) -> str:
    if age is None:
        return "3-6"
    for max_age, label in AGE_GROUPS:
        if age <= max_age:
            return label
    return "7-17"


def _stub_mode() -> bool:
    return not get_settings().openai_api_key


def _openai_client():
    from openai import OpenAI

    return OpenAI(api_key=get_settings().openai_api_key)


def _structured_call(system_prompt: str, user_payload: dict, schema_name: str, json_schema: dict) -> dict:
    import json as _json

    settings = get_settings()
    client = _openai_client()
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        seed=42,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": _json.dumps(user_payload, ensure_ascii=False)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": json_schema},
        },
    )
    return _json.loads(response.choices[0].message.content)


def choose_next_question(answers: list[dict], allowed: list[dict], db=None) -> str | None:
    """Вызов 1 (раздел 12.2): выбор следующего вопроса из allowed."""
    if _stub_mode():
        return stub.choose_next_question(allowed)

    from app.modules.llm.cache import get_cached, store

    payload = {"answers": answers, "allowed": allowed}
    if db is not None:
        cached = get_cached(db, "choose_question", payload)
        if cached:
            return cached["next_question_id"]

    system_prompt = (
        "Ты модуль интервью сервиса, который помогает семье пройти маршрут помощи ребёнку между "
        "медициной, образованием и соцзащитой. Выбери следующий вопрос только из списка allowed. "
        "Сначала вопросы с приоритетом high, затем medium, затем low. Среди равных выбери тот, ответ "
        "на который сильнее всего меняет маршрут семьи с учётом уже данных ответов. Не выбирай Q17 и "
        "Q18, если в allowed есть другие вопросы. Ты не оцениваешь состояние ребёнка и не делаешь "
        "выводов о здоровье. Верни только JSON по схеме."
    )
    schema = {
        "type": "object",
        "properties": {"next_question_id": {"type": "string", "enum": [q["id"] for q in allowed]}},
        "required": ["next_question_id"],
        "additionalProperties": False,
    }
    result = _structured_call(system_prompt, payload, "next_question", schema)
    if db is not None:
        store(db, "choose_question", payload, result)
    return result["next_question_id"]


def parse_q17(text: str, child_name: str | None = None, parent_name: str | None = None, db=None) -> dict:
    """Вызов 2 (раздел 12.2): разбор свободного ответа на Q17."""
    masked = masking.mask_text(text, child_name=child_name, parent_name=parent_name)
    if _stub_mode():
        return stub.parse_q17(masked)

    from app.modules.llm.cache import get_cached, store

    payload = {"text": masked}
    if db is not None:
        cached = get_cached(db, "parse_q17", payload)
        if cached:
            return cached

    system_prompt = (
        "Ты извлекаешь из текста родителя только явно названные ситуации из закрытого списка: "
        "regression (ребёнок перестал делать то, что уже умел), seizures (судороги или потеря "
        "сознания), danger (поведение, опасное для себя или других). Добавляй пункт, только если он "
        "прямо описан в тексте. Не делай выводов о состоянии или диагнозе ребёнка. Определи, с чем "
        "семье нужна помощь в первую очередь, только если это прямо сказано, иначе null. Верни только "
        "JSON по схеме."
    )
    schema = {
        "type": "object",
        "properties": {
            "red_flags": {"type": "array", "items": {"type": "string", "enum": ["regression", "seizures", "danger"]}},
            "priority_focus": {
                "type": ["string", "null"],
                "enum": ["where_to_go", "kindergarten_school", "specialists", "disability_benefits", "documents", None],
            },
        },
        "required": ["red_flags", "priority_focus"],
        "additionalProperties": False,
    }
    result = _structured_call(system_prompt, payload, "parse_q17", schema)
    if db is not None:
        store(db, "parse_q17", payload, result)
    return result


def explain_step(
    service: dict,
    lang: str,
    needs_clarification: bool = False,
    deadline_compressed: bool = False,
    age: int | None = None,
    documents: list | None = None,
    db=None,
) -> str:
    """Вызов 3 (раздел 12.2). В режиме заглушки — шаблон из справочника."""
    if _stub_mode():
        return stub.explain_step(service, lang)

    from app.modules.llm.cache import get_cached, store

    payload = {
        "service_id": service["service_id"],
        "title": service[f"title_{lang}"],
        "agency": service["agency"],
        "age_group": age_group(age),
        "lang": lang,
        "documents": documents or [],
        "needs_clarification": needs_clarification,
        "deadline_compressed": deadline_compressed,
    }

    attempt = 1
    explanation = None
    while attempt <= 2:
        if db is not None:
            cached = get_cached(db, f"explain_step_a{attempt}", payload)
            if cached:
                explanation = cached["explanation"]
            else:
                explanation = _run_explain_prompt(service, lang, payload, attempt)
                store(db, f"explain_step_a{attempt}", payload, {"explanation": explanation})
        else:
            explanation = _run_explain_prompt(service, lang, payload, attempt)

        hits = check_text(explanation, lang=lang)
        if not hits:
            return explanation
        if db is not None:
            from app.models import FilterEvent

            for hit in hits:
                db.add(FilterEvent(call_type="explain_step", service_id=service["service_id"], pattern=hit["pattern"], attempt=attempt))
            db.commit()
        attempt += 1

    return stub.explain_step(service, lang)


def _run_explain_prompt(service: dict, lang: str, payload: dict, attempt: int) -> str:
    system_prompt = (
        f"Ты пишешь объяснение одного шага маршрута для родителя простым языком на языке {lang}. "
        "Два или три предложения, обращение на «вы». Объясни, зачем нужен этот шаг и что семья "
        "получит на выходе. Если deadline_compressed, спокойно объясни, что шаг стоит сделать раньше "
        "обычного, потому что скоро истекает действующий документ. Никогда не утверждай ничего о "
        "здоровье или развитии ребёнка, не называй диагнозы и состояния, не упоминай лекарства, "
        "дозировки и лечение, не делай прогнозов. Для услуг MED_MSE_REFERRAL и SOC_MSE обязательно "
        "скажи, что вопрос об инвалидности решается вместе с врачом. Верни только JSON по схеме."
    )
    if attempt > 1:
        system_prompt += " Предыдущий вариант нарушал правила формулировок, перепиши без нарушений."
    schema = {
        "type": "object",
        "properties": {"explanation": {"type": "string", "maxLength": 400}},
        "required": ["explanation"],
        "additionalProperties": False,
    }
    return _structured_call(system_prompt, payload, "explanation", schema)["explanation"]


def parse_document(text: str, db=None) -> dict:
    """Вызов 4 (раздел 12.2): разбор документа."""
    masked = masking.mask_text(text)
    if _stub_mode():
        return stub.parse_document(masked)

    from app.modules.llm.cache import get_cached, store

    payload = {"text": masked[:4000]}
    if db is not None:
        cached = get_cached(db, "parse_document", payload)
        if cached:
            return cached

    system_prompt = (
        "Ты определяешь тип официального документа и достаёшь из него только реквизиты: тип из "
        "закрытого списка, дату выдачи, дату окончания действия, кем выдан. Если реквизита нет в "
        "тексте, верни null. Не пересказывай и не извлекай медицинское содержание документа. Верни "
        "только JSON по схеме."
    )
    doc_types = ["birth_cert", "pmpk_conclusion", "disability_conclusion", "ipr", "vkk_home", "characteristic", "medical_extract", "child_works", "parent_id"]
    schema = {
        "type": "object",
        "properties": {
            "doc_type": {"type": ["string", "null"], "enum": doc_types + [None]},
            "issued_at": {"type": ["string", "null"]},
            "valid_until": {"type": ["string", "null"]},
            "issuer": {"type": ["string", "null"]},
        },
        "required": ["doc_type", "issued_at", "valid_until", "issuer"],
        "additionalProperties": False,
    }
    result = _structured_call(system_prompt, payload, "parse_document", schema)
    if db is not None:
        store(db, "parse_document", payload, result)
    return result
