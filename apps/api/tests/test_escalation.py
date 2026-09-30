"""Раздел 19.3 SPEC.md: сдвиг времени в кейсе Б, параметризованный тест."""
import json
from datetime import date

import pytest

from app.modules.engine.catalog import get_catalog
from app.modules.engine.engine import build_plan
from app.modules.plans.service import approve_plan, create_draft_plan, get_latest_plan
from app.modules.scheduler.escalation import recompute_family
from app.paths import FIXTURES_DIR
from tests.conftest import make_curator, make_family, make_parent

with open(FIXTURES_DIR / "case_b.json", encoding="utf-8") as f:
    CASE_B = json.load(f)

TABLE_19_3 = [
    (29, "2026-10-30", 0, 0, "2026-12-02"),
    (33, "2026-11-03", 1, 1, "2026-12-03"),
    (35, "2026-11-05", 3, 1, "2026-12-05"),
    (39, "2026-11-09", 7, 2, "2026-12-09"),
    (46, "2026-11-16", 14, 3, "2026-12-16"),
    (50, "2026-11-20", 18, 3, "2026-12-20"),
]


@pytest.mark.parametrize("offset_days,today_str,expected_overdue_days,expected_level,expected_s2_deadline", TABLE_19_3)
def test_time_shift_escalation_levels(db_session, offset_days, today_str, expected_overdue_days, expected_level, expected_s2_deadline):
    catalog = get_catalog()
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)

    steps = build_plan(CASE_B["profile_expected"], catalog, date.fromisoformat(CASE_B["computed_at"]))
    create_draft_plan(db_session, family.id, steps, computed_at=CASE_B["computed_at"])
    approve_plan(db_session, family, curator.id)

    today = date.fromisoformat(today_str)
    recompute_family(db_session, family, catalog, today=today)

    # expire_all форсирует перечитывание из БД, а не из identity map —
    # ловит регрессию "мутация вложенного словаря не долетает до UPDATE".
    db_session.expire_all()
    plan = get_latest_plan(db_session, family.id)
    steps_by_id = {s["step_id"]: s for s in plan.plan_json["steps"]}
    s1 = steps_by_id["S1"]
    s2 = steps_by_id["S2"]

    assert s1["service_id"] == "EDU_PMPK_RENEW"
    deadline = date.fromisoformat(s1["deadline"])
    overdue_days = max((today - deadline).days, 0)
    assert overdue_days == expected_overdue_days
    assert s1["escalation_level"] == expected_level
    if expected_overdue_days >= 1:
        assert s1["status"] == "overdue"

    assert s2["service_id"] == "EDU_ASSISTANT"
    assert s2["deadline"] == expected_s2_deadline
