"""Персистентность и переходы Case Plan (разделы 10.2, 11.4 SPEC.md).

Раздел 11.3 / docs/DECISIONS.md: новая версия создаётся при построении
черновика, при добавлении/удалении шага куратором и при подтверждении.
Изменения статуса шага (11.4), перенос срока и переосчёт планировщиком
меняют текущую версию на месте.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import bad_request, conflict, not_found
from app.models import CasePlan, Family
from app.modules.plans.transitions import validate_transition


def get_latest_plan(db: Session, family_id: int) -> CasePlan | None:
    stmt = (
        select(CasePlan)
        .where(CasePlan.family_id == family_id)
        .order_by(CasePlan.version.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def _next_version(db: Session, family_id: int) -> int:
    latest = get_latest_plan(db, family_id)
    return (latest.version + 1) if latest else 1


def create_draft_plan(
    db: Session, family_id: int, steps: list[dict], computed_at: str, profile_ref: str | None = None
) -> CasePlan:
    version = _next_version(db, family_id)
    plan_json = {
        "case_id": f"C-{family_id:03d}",
        "family_id": str(family_id),
        "version": version,
        "status": "draft",
        "computed_at": computed_at,
        "profile_ref": profile_ref,
        "steps": steps,
        "approved_by": None,
        "approved_at": None,
    }
    row = CasePlan(
        family_id=family_id,
        version=version,
        status="draft",
        plan_json=plan_json,
        created_by="engine",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_plan_for_parent(db: Session, family: Family, user_id: int) -> CasePlan:
    if family.parent_id != user_id:
        raise not_found("Семья не найдена")
    plan = get_latest_plan(db, family.id)
    if plan is None or plan.status == "draft":
        raise not_found("План ещё не готов")
    return plan


def get_plan_for_curator(db: Session, family: Family, user_id: int) -> CasePlan:
    if family.curator_id != user_id:
        raise not_found("Семья не найдена")
    plan = get_latest_plan(db, family.id)
    if plan is None:
        raise not_found("План ещё не построен")
    return plan


def approve_plan(db: Session, family: Family, curator_id: int) -> CasePlan:
    plan = get_plan_for_curator(db, family, curator_id)
    if plan.status != "draft":
        raise conflict("Подтвердить можно только черновик")
    now = datetime.now(timezone.utc)
    new_plan_json = dict(plan.plan_json)
    new_plan_json["status"] = "approved"
    new_plan_json["approved_by"] = curator_id
    new_plan_json["approved_at"] = now.date().isoformat()
    row = CasePlan(
        family_id=family.id,
        version=_next_version(db, family.id),
        status="approved",
        plan_json=new_plan_json,
        created_by="curator",
    )
    # архивируем предыдущую версию явно в её собственном plan_json
    archived_json = dict(plan.plan_json)
    archived_json["status"] = "archived"
    plan.status = "archived"
    plan.plan_json = archived_json
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _mutate_steps_as_new_version(db: Session, family: Family, curator_id: int, mutate) -> CasePlan:
    plan = get_plan_for_curator(db, family, curator_id)
    if plan.status != "draft":
        raise conflict("Менять состав шагов можно только в черновике")
    new_plan_json = dict(plan.plan_json)
    new_plan_json["steps"] = mutate(list(new_plan_json["steps"]))
    row = CasePlan(
        family_id=family.id,
        version=_next_version(db, family.id),
        status="draft",
        plan_json=new_plan_json,
        created_by="curator",
    )
    plan.status = "archived"
    archived_json = dict(plan.plan_json)
    archived_json["status"] = "archived"
    plan.plan_json = archived_json
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def add_step(db: Session, family: Family, curator_id: int, service, wallet: dict | None = None) -> CasePlan:
    """`service` — запись из справочника (уже провалидирован enum'ом на
    уровне Pydantic-схемы запроса, раздел 13: "service_id обязателен,
    проверяется по enum")."""
    from app.modules.engine.engine import DOCUMENT_KINDS

    def mutate(steps):
        existing_ids = {s["service_id"] for s in steps}
        if service["service_id"] in existing_ids:
            raise conflict("Эта услуга уже есть в плане")
        numbers = [int(s["step_id"][1:]) for s in steps if s["step_id"][1:].isdigit()]
        next_number = (max(numbers) + 1) if numbers else 1
        documents = []
        wallet_ = wallet or {}
        for kind in DOCUMENT_KINDS:
            for doc_type in service["documents"][kind]:
                documents.append(
                    {"doc_type": doc_type, "kind": kind, "in_wallet": bool(wallet_.get(doc_type)), "note": None}
                )
        steps.append(
            {
                "step_id": f"S{next_number}",
                "service_id": service["service_id"],
                "title_ru": service["title_ru"],
                "title_kk": service["title_kk"],
                "agency": service["agency"],
                "responsible": service["responsible"],
                "priority": "medium",
                "depends_on": [],
                "start_date": None,
                "deadline": None,
                "original_deadline": None,
                "documents": documents,
                "status": "not_started",
                "explanation_ru": service["explanation_template_ru"],
                "explanation_kk": service["explanation_template_kk"],
                "rule_id": None,
                "source_ids": service["source_ids"],
                "provider_ids": service["provider_ids"],
                "added_by": "curator",
                "needs_clarification": False,
                "deadline_compressed": False,
                "escalation_level": 0,
                "status_history": [],
            }
        )
        return steps

    return _mutate_steps_as_new_version(db, family, curator_id, mutate)


def delete_step(db: Session, family: Family, curator_id: int, step_id: str) -> CasePlan:
    def mutate(steps):
        if not any(s["step_id"] == step_id for s in steps):
            raise not_found(f"Шаг {step_id} не найден")
        return [s for s in steps if s["step_id"] != step_id]

    return _mutate_steps_as_new_version(db, family, curator_id, mutate)


def patch_step_status(
    db: Session,
    family: Family,
    step_id: str,
    new_status: str,
    actor_role: str,
    reason: str | None = None,
    comment: str | None = None,
) -> CasePlan:
    plan = get_latest_plan(db, family.id)
    if plan is None:
        raise not_found("План ещё не построен")
    steps = list(plan.plan_json["steps"])
    step = next((s for s in steps if s["step_id"] == step_id), None)
    if step is None:
        raise not_found(f"Шаг {step_id} не найден")

    validate_transition(
        step["status"], new_status, actor_role, responsible=step["responsible"], reason=reason, comment=comment
    )

    step["status_history"] = list(step.get("status_history", [])) + [
        {
            "from": step["status"],
            "to": new_status,
            "actor_role": actor_role,
            "reason": reason,
            "comment": comment,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    ]
    step["status"] = new_status

    new_plan_json = dict(plan.plan_json)
    new_plan_json["steps"] = steps
    plan.plan_json = new_plan_json
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
