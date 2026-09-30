"""Сроки и эскалация (раздел 11.3 SPEC.md).

Запускается раз в час и при каждом GET /plans/{family}. Текущая дата —
только через `app.clock.today()`.
"""
import copy
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import Escalation, Family, Interview, User
from app.modules.engine.engine import MIN_DAYS, parse_profile_date
from app.modules.notifications.service import notify
from app.modules.plans.service import get_latest_plan

OPEN_STATUSES = ("not_started", "in_progress", "blocked")
DONE_STATUSES = ("done", "done_by_parent")

# Раздел 11.3, таблица уровней.
LEVEL_CHANNELS = {
    0: ["center", "email"],
    1: ["center", "email"],
    2: ["center"],
    3: ["center"],
}


def _target_level(deadline: date, today: date, overdue_days: int) -> int | None:
    if overdue_days >= 14:
        return 3
    if overdue_days >= 7:
        return 2
    if overdue_days >= 1:
        return 1
    if (deadline - today).days <= 3:
        return 0
    return None


def _get(profile, path):
    node = profile
    for part in path.split("."):
        if node is None:
            return None
        node = node.get(part)
    return node


def _recompute_step_deadline(step: dict, catalog, today: date, profile: dict | None):
    service = catalog.services.get(step["service_id"])
    if service is None:
        return
    sla = service["sla"]
    start_date = today
    if sla["type"] == "days":
        new_deadline = start_date + timedelta(days=sla["value"])
    elif sla["type"] == "before_field":
        field_date = parse_profile_date(_get(profile or {}, sla["field"]))
        if field_date:
            new_deadline = field_date - timedelta(days=sla["days"])
        else:
            new_deadline = start_date + timedelta(days=MIN_DAYS.get(step["service_id"], sla["days"]))
    else:
        return
    min_days = MIN_DAYS.get(step["service_id"])
    if min_days is not None:
        min_deadline = start_date + timedelta(days=min_days)
        if new_deadline < min_deadline:
            new_deadline = min_deadline
    step["start_date"] = start_date.isoformat()
    step["deadline"] = new_deadline.isoformat()


def recompute_family(db: Session, family: Family, catalog, today: date | None = None) -> dict:
    from app import clock

    today = today or clock.today(db)
    plan = get_latest_plan(db, family.id)
    if plan is None or plan.status not in ("draft", "approved"):
        return {"changed": False}

    steps = copy.deepcopy(plan.plan_json["steps"])
    steps_by_id = {s["step_id"]: s for s in steps}
    newly_overdue = set()
    changed = False

    for step in steps:
        if step["status"] in DONE_STATUSES:
            continue
        deadline = date.fromisoformat(step["deadline"])
        overdue_days = (today - deadline).days
        if overdue_days >= 1 and step["status"] in OPEN_STATUSES and step["status"] != "overdue":
            step["status_history"] = list(step.get("status_history", [])) + [
                {"from": step["status"], "to": "overdue", "actor_role": "system", "ts": today.isoformat()}
            ]
            step["status"] = "overdue"
            newly_overdue.add(step["step_id"])
            changed = True

        target = _target_level(deadline, today, max(overdue_days, 0))
        current_level = step.get("escalation_level", 0)
        if target is not None and target > current_level:
            for level in range(current_level + 1, target + 1):
                exists = (
                    db.query(Escalation)
                    .filter(
                        Escalation.family_id == family.id,
                        Escalation.step_id == step["step_id"],
                        Escalation.level == level,
                    )
                    .one_or_none()
                )
                if exists:
                    continue
                appeal_text = None
                if level == 3:
                    appeal_text = _build_appeal_text(step, catalog, deadline, overdue_days)
                db.add(
                    Escalation(
                        family_id=family.id,
                        step_id=step["step_id"],
                        level=level,
                        appeal_text=appeal_text,
                    )
                )
                _notify_escalation(db, family, step, level)
            step["escalation_level"] = target
            changed = True

    if newly_overdue:
        interview = (
            db.query(Interview)
            .filter(Interview.family_id == family.id, Interview.finished_at.isnot(None))
            .order_by(Interview.id.desc())
            .first()
        )
        profile = interview.profile if interview else None
        order = _topo_order(steps_by_id)
        for step_id in order:
            step = steps_by_id[step_id]
            if step["status"] in DONE_STATUSES:
                continue
            blocking_overdue = any(
                steps_by_id[d]["status"] not in DONE_STATUSES
                and (d in newly_overdue or steps_by_id[d].get("_recomputed"))
                for d in step["depends_on"]
            )
            if blocking_overdue:
                _recompute_step_deadline(step, catalog, today, profile)
                step["_recomputed"] = True
                changed = True
        for step in steps:
            step.pop("_recomputed", None)

    if changed:
        new_plan_json = dict(plan.plan_json)
        new_plan_json["steps"] = steps
        plan.plan_json = new_plan_json
        db.add(plan)
        db.commit()
        db.refresh(plan)

    return {"changed": changed, "plan": plan}


def revert_time_shift(db: Session, family: Family) -> None:
    """Демо-сброс (раздел 15.2): откатить то, что сделал пересчёт после
    сдвига времени, — системные переходы в overdue, уровни эскалации и сроки
    шагов, пересчитанные из-за просроченной зависимости."""
    plan = get_latest_plan(db, family.id)
    if plan is None or plan.status not in ("draft", "approved"):
        return
    steps = copy.deepcopy(plan.plan_json["steps"])
    system_overdue = set()
    for step in steps:
        history = list(step.get("status_history", []))
        auto = [h for h in history if h.get("actor_role") == "system" and h.get("to") == "overdue"]
        if auto:
            system_overdue.add(step["step_id"])
            if step["status"] == "overdue":
                step["status"] = auto[0]["from"]
            step["status_history"] = [h for h in history if h not in auto]
        step["escalation_level"] = 0
    for step in steps:
        if step.get("original_deadline") and any(d in system_overdue for d in step["depends_on"]):
            step["deadline"] = step["original_deadline"]
    new_plan_json = dict(plan.plan_json)
    new_plan_json["steps"] = steps
    plan.plan_json = new_plan_json
    db.add(plan)
    db.commit()


def _topo_order(steps_by_id: dict) -> list[str]:
    order = []
    visited = set()

    def visit(sid):
        if sid in visited:
            return
        visited.add(sid)
        for dep in steps_by_id[sid]["depends_on"]:
            if dep in steps_by_id:
                visit(dep)
        order.append(sid)

    for sid in steps_by_id:
        visit(sid)
    return order


def _build_appeal_text(step: dict, catalog, deadline: date, overdue_days: int) -> str:
    service = catalog.services.get(step["service_id"], {})
    sources = ", ".join(step.get("source_ids") or []) or "нет подтверждённого источника"
    return (
        f"Ведомство: {step['agency']}. Услуга: {step.get('title_ru', service.get('title_ru', step['service_id']))}. "
        f"Регламентный срок истёк {deadline.isoformat()} (источник: {sources}). "
        f"Просрочка: {overdue_days} дн."
    )


def _notify_escalation(db: Session, family: Family, step: dict, level: int):
    payload = {"family_id": family.id, "step_id": step["step_id"], "service_id": step["service_id"], "level": level}
    channels = LEVEL_CHANNELS.get(level, ["center"])
    curator = db.get(User, family.curator_id) if family.curator_id else None
    parent = db.get(User, family.parent_id) if family.parent_id else None
    notif_type = f"escalation_{level}"
    if level == 0:
        responsible_user = curator if step["responsible"] == "education_org" else parent
        notify(db, responsible_user, notif_type, payload, channels)
    elif level == 1:
        notify(db, parent, notif_type, payload, channels)
        notify(db, curator, notif_type, payload, channels)
    else:
        notify(db, curator, notif_type, payload, channels)
