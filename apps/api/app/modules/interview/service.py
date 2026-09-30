"""Оркестрация интервью поверх БД (раздел 11.1 SPEC.md)."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import clock
from app.errors import bad_request, conflict, not_found
from app.models import Interview, User
from app.modules.engine.catalog import get_catalog
from app.modules.engine.engine import build_plan
from app.modules.interview import flow
from app.modules.llm import client as llm_client
from app.modules.notifications.service import notify
from app.modules.plans.service import create_draft_plan

LANGS = ("ru", "kk")


def _get_or_create_interview(db: Session, family_id: int) -> Interview:
    stmt = select(Interview).where(Interview.family_id == family_id, Interview.finished_at.is_(None))
    interview = db.execute(stmt).scalars().first()
    if interview is None:
        interview = Interview(family_id=family_id, answers=[], profile={}, unknown_fields=[])
        db.add(interview)
        db.commit()
        db.refresh(interview)
    return interview


def _answers_dict(interview: Interview) -> dict:
    return {a["question_id"]: a["value"] for a in interview.answers}


def start(db: Session, family_id: int) -> dict:
    catalog = get_catalog()
    interview = _get_or_create_interview(db, family_id)
    answers = _answers_dict(interview)
    state = flow.compute_next(catalog.questions, answers)
    if state["done"]:
        return {"done": True}
    question = catalog.questions[state["question_id"]]
    return {"done": False, "question": question}


def answer(db: Session, family_id: int, question_id: str, value) -> dict:
    catalog = get_catalog()
    interview = _get_or_create_interview(db, family_id)
    if interview.finished_at is not None:
        raise conflict("Интервью уже завершено")
    answers = _answers_dict(interview)
    if question_id not in catalog.questions:
        raise bad_request(f"Неизвестный вопрос {question_id}")
    question = catalog.questions[question_id]
    allowed_ids = {q["id"] for q in flow.compute_allowed(catalog.questions, answers)}
    if question_id in answers:
        raise conflict(f"На вопрос {question_id} уже отвечено")
    if question_id not in allowed_ids:
        raise conflict(f"Вопрос {question_id} сейчас не допустим")

    validated = flow.validate_answer(question, value)

    new_answers = list(interview.answers) + [
        {"question_id": question_id, "value": validated, "answered_at": datetime.now(timezone.utc).isoformat()}
    ]
    interview.answers = new_answers
    db.add(interview)
    db.commit()
    db.refresh(interview)

    state = flow.compute_next(catalog.questions, _answers_dict(interview))
    if state["done"]:
        return {"done": True}
    return {"done": False, "question": catalog.questions[state["question_id"]]}


def back(db: Session, family_id: int) -> dict:
    catalog = get_catalog()
    interview = _get_or_create_interview(db, family_id)
    if interview.finished_at is not None:
        raise conflict("Интервью уже завершено")
    if not interview.answers:
        raise conflict("Нет ответов для отмены")
    interview.answers = list(interview.answers)[:-1]
    db.add(interview)
    db.commit()
    db.refresh(interview)

    state = flow.compute_next(catalog.questions, _answers_dict(interview))
    if state["done"]:
        return {"done": True}
    return {"done": False, "question": catalog.questions[state["question_id"]]}


def finish(db: Session, family_id: int) -> dict:
    catalog = get_catalog()
    interview = _get_or_create_interview(db, family_id)
    if interview.finished_at is not None:
        raise conflict("Интервью уже завершено")
    answers = _answers_dict(interview)
    if len(answers) < flow.MIN_ANSWERS_TO_FINISH:
        raise conflict(f"Нужно минимум {flow.MIN_ANSWERS_TO_FINISH} ответов")

    profile = flow.build_profile(catalog.questions, answers)

    if "Q17" in answers:
        parsed = llm_client.parse_q17(answers["Q17"])
        profile = flow.merge_q17_flags(profile, parsed)

    interview.profile = profile
    interview.unknown_fields = profile["unknown_fields"]
    interview.finished_at = datetime.now(timezone.utc)
    db.add(interview)
    db.commit()
    db.refresh(interview)

    computed_at = clock.today(db)
    steps = build_plan(profile, catalog, computed_at)
    for step in steps:
        service = catalog.services[step["service_id"]]
        for lang in LANGS:
            step[f"explanation_{lang}"] = llm_client.explain_step(
                service, lang, needs_clarification=step["needs_clarification"], deadline_compressed=step["deadline_compressed"]
            )

    plan = create_draft_plan(
        db,
        family_id,
        steps,
        computed_at=computed_at.isoformat(),
        profile_ref=f"I-{interview.id:03d}",
    )

    from app.models import Family

    family = db.get(Family, family_id)
    curator = db.get(User, family.curator_id) if family and family.curator_id else None
    notify(db, curator, "draft_ready", {"family_id": family_id}, ["center", "email"])
    if any(f != "none" for f in (profile.get("red_flags") or [])):
        notify(db, curator, "red_flag", {"family_id": family_id, "red_flags": profile["red_flags"]}, ["center", "email"])

    return {"done": True, "plan_version": plan.version, "profile": profile}
