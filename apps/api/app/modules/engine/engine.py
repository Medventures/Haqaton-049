"""Движок правил (раздел 11.2 SPEC.md).

`build_plan(profile, catalog, computed_at, wallet=None) -> list[dict]` —
чистая функция: без обращений к БД, сети и LLM. Объяснения к шагам не
часть движка (их добавляет модуль LLM после построения).
"""
from datetime import date, timedelta

from app.modules.engine.rules import PRIORITY_RANK, apply_r15, run_rules

# Раздел 11.2, пункт 3: минимальный срок для сжатия дедлайна.
# Определён только для услуг с sla.type = before_field.
MIN_DAYS = {
    "EDU_PMPK_RENEW": 32,
    "SOC_DISABILITY_REVIEW": 30,
}

DOCUMENT_KINDS = ["required", "if_present", "on_request", "agency_requests"]


class EngineError(Exception):
    def __init__(self, message, rule_id=None):
        super().__init__(message)
        self.rule_id = rule_id
        self.message = message


def _get(profile, path):
    node = profile
    for part in path.split("."):
        if node is None:
            return None
        node = node.get(part)
    return node


def _build_documents(service, profile, wallet):
    docs_present = set(_get(profile, "docs.present") or [])
    wallet = wallet or {}
    documents = []
    for kind in DOCUMENT_KINDS:
        for doc_type in service["documents"][kind]:
            in_wallet = doc_type in docs_present or bool(wallet.get(doc_type))
            documents.append(
                {
                    "doc_type": doc_type,
                    "kind": kind,
                    "in_wallet": in_wallet,
                    "note": None,
                }
            )
    return documents


def _compute_dates(profile, computed_at, catalog, added):
    depends_on_map = {
        sid: [p for p in catalog.services[sid]["predecessors_any"] if p in added]
        for sid in added
    }
    start = {}
    deadline = {}
    priority = {sid: added[sid]["priority"] for sid in added}
    flags = {sid: dict(added[sid]["flags"]) for sid in added}

    visiting = set()
    done = set()

    def visit(sid):
        if sid in done:
            return
        if sid in visiting:
            raise EngineError(f"Цикл зависимостей на услуге {sid}", rule_id=None)
        visiting.add(sid)
        for dep in depends_on_map[sid]:
            visit(dep)
        visiting.discard(sid)

        deps_deadlines = [deadline[d] for d in depends_on_map[sid]]
        start_date = max([computed_at] + deps_deadlines)

        service = catalog.services[sid]
        sla = service["sla"]
        if sla["type"] == "days":
            dl = start_date + timedelta(days=sla["value"])
        elif sla["type"] == "before_field":
            field_value = _get(profile, sla["field"])
            if field_value:
                field_date = date.fromisoformat(field_value)
                dl = field_date - timedelta(days=sla["days"])
            else:
                min_days = MIN_DAYS.get(sid, sla["days"])
                dl = start_date + timedelta(days=min_days)
                flags[sid]["needs_clarification"] = True
        else:
            raise EngineError(f"Неизвестный тип sla у {sid}: {sla['type']}")

        if sid in MIN_DAYS:
            min_deadline = start_date + timedelta(days=MIN_DAYS[sid])
            if dl < min_deadline:
                dl = min_deadline
                priority[sid] = "critical"
                flags[sid]["deadline_compressed"] = True

        start[sid] = start_date
        deadline[sid] = dl
        done.add(sid)

    for sid in list(added.keys()):
        visit(sid)

    return start, deadline, priority, flags, depends_on_map


def build_plan(profile, catalog, computed_at, wallet=None):
    if isinstance(computed_at, str):
        computed_at = date.fromisoformat(computed_at)

    added = run_rules(profile, computed_at, catalog)
    if not added:
        return []

    start, deadline, priority, flags, depends_on_map = _compute_dates(
        profile, computed_at, catalog, added
    )

    documents_by_service = {
        sid: _build_documents(catalog.services[sid], profile, wallet) for sid in added
    }
    apply_r15(profile, documents_by_service)

    ordered = sorted(
        added.keys(),
        key=lambda sid: (PRIORITY_RANK[priority[sid]], deadline[sid].isoformat(), sid),
    )
    step_id_of = {sid: f"S{i + 1}" for i, sid in enumerate(ordered)}

    steps = []
    for sid in ordered:
        service = catalog.services[sid]
        step_flags = flags[sid]
        depends_on_steps = [step_id_of[dep] for dep in depends_on_map[sid]]
        step = {
            "step_id": step_id_of[sid],
            "service_id": sid,
            "title_ru": service["title_ru"],
            "title_kk": service["title_kk"],
            "agency": service["agency"],
            "responsible": service["responsible"],
            "priority": priority[sid],
            "depends_on": depends_on_steps,
            "start_date": start[sid].isoformat(),
            "deadline": deadline[sid].isoformat(),
            "original_deadline": deadline[sid].isoformat(),
            "documents": documents_by_service[sid],
            "status": "blocked" if depends_on_steps else "not_started",
            "explanation_ru": None,
            "explanation_kk": None,
            "rule_id": added[sid]["rule_id"],
            "source_ids": service["source_ids"],
            "provider_ids": service["provider_ids"],
            "added_by": "engine",
            "needs_clarification": bool(step_flags.get("needs_clarification", False)),
            "deadline_compressed": bool(step_flags.get("deadline_compressed", False)),
            "escalation_level": 0,
            "status_history": [],
        }
        for field in ("priority", "responsible", "deadline", "documents", "status"):
            if step[field] in (None, ""):
                raise EngineError(
                    f"Шаг {step['step_id']} ({sid}): не заполнено поле {field}",
                    rule_id=added[sid]["rule_id"],
                )
        if sid not in catalog.services:
            raise EngineError(f"Услуга {sid} отсутствует в справочнике")
        steps.append(step)

    return steps
