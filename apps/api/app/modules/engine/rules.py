"""Правила движка (раздел 7 SPEC.md).

Каждая функция `rule_Rxx` — чистая функция от профиля, даты расчёта,
справочника и уже добавленных услуг (`added_so_far`, только для чтения).
Возвращает список `RuleHit`. Порядок вызова R01..R14 задаёт функция
`run_rules` — она же разрешает конфликт, если одна услуга добавлена
несколькими правилами (раздел 11.2, пункт 1).

R15 не добавляет шаг, поэтому реализован отдельно в engine.py.
"""
from collections import namedtuple
from datetime import timedelta

RuleHit = namedtuple("RuleHit", ["service_id", "priority", "flags"])


def _hit(service_id, priority, **flags):
    return RuleHit(service_id, priority, flags)


def _get(profile, path):
    node = profile
    for part in path.split("."):
        if node is None:
            return None
        node = node.get(part)
    return node


def rule_r01(profile, computed_at, catalog, added_so_far):
    red_flags = _get(profile, "red_flags") or []
    if any(flag != "none" for flag in red_flags):
        return [_hit("MED_URGENT", "critical")]
    return []


def rule_r02(profile, computed_at, catalog, added_so_far):
    if _get(profile, "child.doctor_conclusion") in ("no", "in_progress"):
        return [_hit("MED_DEV_CONSULT", "high")]
    return []


def rule_r03(profile, computed_at, catalog, added_so_far):
    age = _get(profile, "child.age")
    age_window = catalog.services["EDU_EARLY_HELP"]["age_window"]
    max_age = age_window["max_age"] if age_window else None
    if age is not None and max_age is not None and age <= max_age:
        return [_hit("EDU_EARLY_HELP", "high")]
    return []


def rule_r04(profile, computed_at, catalog, added_so_far):
    age = _get(profile, "child.age")
    status = _get(profile, "pmpk.status")
    unknown_fields = profile.get("unknown_fields") or []
    status_unknown = "pmpk.status" in unknown_fields
    if age is not None and age >= 2 and (status in ("no", "expired", "unknown") or status_unknown):
        needs_clarification = status == "unknown" or status_unknown
        return [_hit("EDU_PMPK", "high", needs_clarification=needs_clarification)]
    return []


def rule_r05(profile, computed_at, catalog, added_so_far):
    status = _get(profile, "pmpk.status")
    change_planned = _get(profile, "education.change_planned")
    if status == "expiring" or (status == "valid" and change_planned == "yes"):
        return [_hit("EDU_PMPK_RENEW", "high")]
    return []


def rule_r06(profile, computed_at, catalog, added_so_far):
    if "EDU_PMPK" not in added_so_far and "EDU_PMPK_RENEW" not in added_so_far:
        return []
    day_place = _get(profile, "child.day_place")
    docs_present = _get(profile, "docs.present") or []
    if day_place in ("kindergarten", "school") and "characteristic" not in docs_present:
        return [_hit("EDU_CHARACTERISTIC", "medium")]
    return []


def rule_r07(profile, computed_at, catalog, added_so_far):
    recommendations = _get(profile, "pmpk.recommendations") or []
    if "assistant" in recommendations:
        return [_hit("EDU_ASSISTANT", "high")]
    return []


def rule_r08(profile, computed_at, catalog, added_so_far):
    recommendations = _get(profile, "pmpk.recommendations") or []
    support = _get(profile, "support.current") or []
    if "kppk" in recommendations and "kppk" not in support:
        return [_hit("EDU_KPPK", "medium")]
    return []


def rule_r09(profile, computed_at, catalog, added_so_far):
    recommendations = _get(profile, "pmpk.recommendations") or []
    disability_status = _get(profile, "disability.status")
    support = _get(profile, "support.current") or []
    condition = "rehab" in recommendations or disability_status == "yes_with_ipr"
    already_supported = "rehab" in support or "asd_center" in support
    if condition and not already_supported:
        return [_hit("SOC_REHAB", "medium")]
    return []


def rule_r10(profile, computed_at, catalog, added_so_far):
    if _get(profile, "education.change_planned") == "yes":
        return [_hit("EDU_ENROLL", "high")]
    return []


def rule_r11(profile, computed_at, catalog, added_so_far):
    docs_present = _get(profile, "docs.present") or []
    if _get(profile, "education.home_learning_need") == "home_recommended" and "vkk_home" not in docs_present:
        return [_hit("MED_VKK_HOME", "medium")]
    return []


def rule_r12(profile, computed_at, catalog, added_so_far):
    if _get(profile, "child.doctor_conclusion") == "yes" and _get(profile, "disability.status") == "no":
        return [_hit("MED_MSE_REFERRAL", "medium"), _hit("SOC_MSE", "medium")]
    return []


def rule_r13(profile, computed_at, catalog, added_so_far):
    disability_status = _get(profile, "disability.status")
    r12_fired = "MED_MSE_REFERRAL" in added_so_far or "SOC_MSE" in added_so_far
    benefits = _get(profile, "social.benefits") or []
    benefits_unresolved = not benefits or "none" in benefits or "unknown" in benefits
    if (disability_status in ("yes_with_ipr", "yes_no_ipr") or r12_fired) and benefits_unresolved:
        return [_hit("SOC_BENEFITS", "medium")]
    return []


def rule_r14(profile, computed_at, catalog, added_so_far):
    review_date = _get(profile, "disability.review_date")
    if not review_date:
        return []
    from datetime import date as _date
    d = _date.fromisoformat(review_date)
    if d <= computed_at + timedelta(days=90):
        return [_hit("SOC_DISABILITY_REVIEW", "high")]
    return []


RULES = [
    ("R01", rule_r01),
    ("R02", rule_r02),
    ("R03", rule_r03),
    ("R04", rule_r04),
    ("R05", rule_r05),
    ("R06", rule_r06),
    ("R07", rule_r07),
    ("R08", rule_r08),
    ("R09", rule_r09),
    ("R10", rule_r10),
    ("R11", rule_r11),
    ("R12", rule_r12),
    ("R13", rule_r13),
    ("R14", rule_r14),
]

PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _higher_priority(a, b):
    return a if PRIORITY_RANK[a] <= PRIORITY_RANK[b] else b


def run_rules(profile, computed_at, catalog):
    """Возвращает {service_id: {"rule_id", "priority", "flags"}}."""
    added = {}
    for rule_id, rule_fn in RULES:
        for hit in rule_fn(profile, computed_at, catalog, added):
            existing = added.get(hit.service_id)
            if existing is None:
                added[hit.service_id] = {
                    "rule_id": rule_id,
                    "priority": hit.priority,
                    "flags": dict(hit.flags),
                }
            else:
                existing["priority"] = _higher_priority(existing["priority"], hit.priority)
                existing["flags"].update(hit.flags)
    return added


def apply_r15(profile, added_services_documents):
    """Раздел 7, R15: не шаг, а пометка к документу birth_cert.

    `added_services_documents` — {service_id: [document dict, ...]} для
    услуг, уже добавленных в план (мутируется на месте).
    """
    if _get(profile, "docs.birth_abroad") is not True:
        return
    for service_id in ("EDU_PMPK", "EDU_PMPK_RENEW"):
        documents = added_services_documents.get(service_id)
        if not documents:
            continue
        for doc in documents:
            if doc["doc_type"] == "birth_cert":
                doc["note"] = "electronic_copy_required"
