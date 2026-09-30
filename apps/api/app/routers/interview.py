from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.deps import get_family_for_curator, get_own_family_for_parent
from app.errors import bad_request, not_found
from app.models import Clarification, Interview, User
from app.modules.engine.catalog import get_catalog
from app.modules.interview import service as interview_service

router = APIRouter(prefix="/interview", tags=["interview"])


class AnswerRequest(BaseModel):
    question_id: str
    value: object


class ClarifyRequest(BaseModel):
    question_id: str


def _question_payload(question: dict | None):
    if question is None:
        return None
    return {
        "id": question["id"],
        "text_ru": question["text_ru"],
        "text_kk": question["text_kk"],
        "hint_ru": question["hint_ru"],
        "hint_kk": question["hint_kk"],
        "answer_type": question["answer_type"],
        "options": question["options"],
        "min": question.get("min"),
        "max": question.get("max"),
        "max_length": question.get("max_length"),
    }


def _result(state: dict):
    if state["done"]:
        return {"done": True, **{k: v for k, v in state.items() if k != "done"}}
    return {"done": False, "question": _question_payload(state["question"])}


@router.post("/start")
def start(db: Session = Depends(get_db), parent: User = Depends(require_role("parent"))):
    family = get_own_family_for_parent(db, parent)
    return _result(interview_service.start(db, family.id))


@router.post("/answer")
def answer(body: AnswerRequest, db: Session = Depends(get_db), parent: User = Depends(require_role("parent"))):
    family = get_own_family_for_parent(db, parent)
    return _result(interview_service.answer(db, family.id, body.question_id, body.value))


@router.post("/back")
def back(db: Session = Depends(get_db), parent: User = Depends(require_role("parent"))):
    family = get_own_family_for_parent(db, parent)
    return _result(interview_service.back(db, family.id))


@router.post("/finish")
def finish(db: Session = Depends(get_db), parent: User = Depends(require_role("parent"))):
    family = get_own_family_for_parent(db, parent)
    return interview_service.finish(db, family.id)


@router.get("/{family_id}")
def get_interview(family_id: int, db: Session = Depends(get_db), curator: User = Depends(require_role("curator"))):
    family = get_family_for_curator(db, family_id, curator)
    interview = (
        db.query(Interview)
        .filter(Interview.family_id == family.id)
        .order_by(Interview.id.desc())
        .first()
    )
    if interview is None:
        raise not_found("Интервью ещё не начато")
    return {
        "answers": interview.answers,
        "profile": interview.profile,
        "unknown_fields": interview.unknown_fields,
        "finished_at": interview.finished_at,
    }


@router.post("/{family_id}/clarify")
def clarify(
    family_id: int,
    body: ClarifyRequest,
    db: Session = Depends(get_db),
    curator: User = Depends(require_role("curator")),
):
    family = get_family_for_curator(db, family_id, curator)
    catalog = get_catalog()
    interview = (
        db.query(Interview)
        .filter(Interview.family_id == family.id)
        .order_by(Interview.id.desc())
        .first()
    )
    if interview is None:
        raise not_found("Интервью ещё не начато")
    profile_fields = {catalog.questions[qid]["profile_field"]: qid for qid in catalog.questions if qid == body.question_id}
    if body.question_id not in catalog.questions:
        raise bad_request(f"Неизвестный вопрос {body.question_id}")
    question = catalog.questions[body.question_id]
    if question["profile_field"] not in (interview.unknown_fields or []):
        raise bad_request("Этот вопрос не входит в unknown_fields")

    row = Clarification(family_id=family.id, question_id=body.question_id, asked_by=curator.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "question_id": row.question_id, "asked_at": row.asked_at}
