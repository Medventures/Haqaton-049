"""Интервью (раздел 11.1 SPEC.md): чистая логика без обращения к БД/LLM.

`InterviewFlowError` — ошибки валидации ответа (маппятся на HTTP 422 в
роутере).
"""
from datetime import date

from app.modules.llm import client as llm_client

MANDATORY_ORDER = ["Q01", "Q02", "Q03", "Q04", "Q14", "Q16"]
MAX_ANSWERS = 12
MIN_ANSWERS_TO_FINISH = 8
FILLER_QUESTIONS = ("Q17", "Q18")

# Раздел 5.2: "истина, если ответ no" — Q15 не передаётся в профиль как
# есть, а трансформируется в булево docs.birth_abroad.
_PROFILE_TRANSFORMS = {
    "Q15": lambda value: value == "no",
}


class InterviewFlowError(ValueError):
    pass


def eval_condition(node, answers: dict) -> bool:
    if isinstance(node, str):
        # "always" и "filler" — вопрос всегда кандидат в allowed.
        return True
    if "any" in node:
        return any(eval_condition(c, answers) for c in node["any"])
    if "all" in node:
        return all(eval_condition(c, answers) for c in node["all"])
    q, op, value = node["q"], node["op"], node["value"]
    if q not in answers:
        return False
    actual = answers[q]
    if op == "eq":
        return actual == value
    if op == "in":
        return actual in value
    if op == "gte":
        return actual is not None and actual >= value
    if op == "lt":
        return actual is not None and actual < value
    if op == "contains":
        return isinstance(actual, list) and value in actual
    if op == "not_contains":
        return not (isinstance(actual, list) and value in actual)
    raise InterviewFlowError(f"Неизвестный оператор show_if: {op}")


def is_filler(question: dict) -> bool:
    return question["show_if"] == "filler"


def compute_allowed(questions_by_id: dict, answers: dict) -> list[dict]:
    return [
        q
        for qid, q in questions_by_id.items()
        if qid not in answers and eval_condition(q["show_if"], answers)
    ]


def validate_answer(question: dict, value):
    answer_type = question["answer_type"]

    if answer_type == "number":
        if not isinstance(value, int) or isinstance(value, bool):
            raise InterviewFlowError(f"{question['id']}: ожидалось целое число")
        lo, hi = question.get("min", 0), question.get("max", 17)
        if not (lo <= value <= hi):
            raise InterviewFlowError(f"{question['id']}: значение вне диапазона [{lo}, {hi}]")
        return value

    if answer_type == "single":
        codes = {o["code"] for o in question["options"]}
        if value not in codes:
            raise InterviewFlowError(f"{question['id']}: недопустимый код '{value}'")
        return value

    if answer_type == "multi":
        codes = {o["code"] for o in question["options"]}
        if not isinstance(value, list) or not value:
            raise InterviewFlowError(f"{question['id']}: ожидался непустой список кодов")
        for code in value:
            if code not in codes:
                raise InterviewFlowError(f"{question['id']}: недопустимый код '{code}'")
        if "none" in value and "none" in codes:
            return ["none"]
        return value

    if answer_type == "date_or_unknown":
        if value == "unknown":
            return value
        try:
            date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise InterviewFlowError(f"{question['id']}: ожидалась дата ISO или 'unknown'") from exc
        return value

    if answer_type == "text":
        max_length = question.get("max_length", 500)
        if not isinstance(value, str) or not value.strip():
            raise InterviewFlowError(f"{question['id']}: ожидался непустой текст")
        if len(value) > max_length:
            raise InterviewFlowError(f"{question['id']}: текст длиннее {max_length} символов")
        return value

    raise InterviewFlowError(f"{question['id']}: неизвестный answer_type '{answer_type}'")


def _fallback_pick(allowed: list[dict]) -> str:
    rank = {"mandatory": 0, "high": 1, "medium": 2, "low": 3}
    non_filler = [q for q in allowed if q["id"] not in FILLER_QUESTIONS]
    pool = non_filler if non_filler else allowed
    ordered = sorted(pool, key=lambda q: (rank.get(q["priority"], 9), q["id"]))
    return ordered[0]["id"]


def compute_next(questions_by_id: dict, answers: dict) -> dict:
    """Возвращает {"done": True} либо {"done": False, "question_id": ...}."""
    answered_count = len(answers)
    if answered_count >= MAX_ANSWERS:
        return {"done": True}

    allowed = compute_allowed(questions_by_id, answers)
    allowed_ids = {q["id"] for q in allowed}

    for qid in MANDATORY_ORDER:
        if qid in allowed_ids:
            return {"done": False, "question_id": qid}

    non_filler_allowed = [q for q in allowed if q["id"] not in FILLER_QUESTIONS]
    if not non_filler_allowed and answered_count >= MIN_ANSWERS_TO_FINISH:
        return {"done": True}

    if not allowed:
        for filler_id in FILLER_QUESTIONS:
            if filler_id not in answers:
                return {"done": False, "question_id": filler_id}
        return {"done": True}

    llm_input = [{"id": q["id"], "priority": q["priority"]} for q in allowed]
    chosen = llm_client.choose_next_question(list(answers.items()), llm_input)
    if chosen not in allowed_ids:
        chosen = _fallback_pick(allowed)
    return {"done": False, "question_id": chosen}


def compute_unknown_fields(questions_by_id: dict, answers: dict) -> list[str]:
    allowed = compute_allowed(questions_by_id, answers)
    return [q["profile_field"] for q in allowed if not is_filler(q)]


def build_profile(questions_by_id: dict, answers: dict) -> dict:
    profile = {
        "child": {"age": None, "doctor_conclusion": None, "day_place": None},
        "family": {"region": None},
        "pmpk": {"status": None, "recommendations": None, "valid_until": None},
        "education": {"change_planned": None, "home_learning_need": None},
        "disability": {"status": None, "review_date": None},
        "social": {"benefits": None},
        "support": {"current": None},
        "docs": {"present": None, "birth_abroad": None},
        "red_flags": None,
        "concerns": None,
        "priority_focus": None,
        "unknown_fields": [],
    }
    for qid, value in answers.items():
        question = questions_by_id[qid]
        transform = _PROFILE_TRANSFORMS.get(qid)
        stored_value = transform(value) if transform else value
        path = question["profile_field"].split(".")
        node = profile
        for part in path[:-1]:
            node = node[part]
        node[path[-1]] = stored_value

    profile["unknown_fields"] = compute_unknown_fields(questions_by_id, answers)
    return profile


def merge_q17_flags(profile: dict, parsed: dict) -> dict:
    """Раздел 11.1: флаги из Q17 добавляются в red_flags с пометкой
    источника from_text и показываются куратору отдельно."""
    from_text = [f for f in parsed.get("red_flags", []) if f]
    if from_text:
        current = list(profile.get("red_flags") or [])
        merged = [f for f in current if f != "none"]
        for flag in from_text:
            if flag not in merged:
                merged.append(flag)
        profile["red_flags"] = merged or ["none"]
        profile["red_flags_from_text"] = from_text
    if parsed.get("priority_focus") and not profile.get("priority_focus"):
        profile["priority_focus"] = parsed["priority_focus"]
    return profile
