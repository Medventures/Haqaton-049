"""К16 (раздел 20): оба кейса проходят полный цикл до эскалации уровня 3.

test_escalation.py уже покрывает это для кейса Б (таблица 19.3). Раздел
19.4 (демо-сценарий) для кейса А останавливается на шаге 4 (фильтр),
эскалация явно не расписана — но К16 требует полного цикла для обоих
кейсов, так что проверяем то же самое для кейса А отдельно.
"""
import json
from datetime import date

from app.modules.engine.catalog import get_catalog
from app.modules.engine.engine import build_plan
from app.modules.plans.service import approve_plan, create_draft_plan, get_latest_plan
from app.modules.scheduler.escalation import recompute_family
from app.paths import FIXTURES_DIR
from tests.conftest import make_curator, make_family, make_parent

with open(FIXTURES_DIR / "case_a.json", encoding="utf-8") as f:
    CASE_A = json.load(f)


def test_case_a_reaches_escalation_level_3(db_session):
    catalog = get_catalog()
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)

    steps = build_plan(CASE_A["profile_expected"], catalog, date.fromisoformat(CASE_A["computed_at"]))
    create_draft_plan(db_session, family.id, steps, computed_at=CASE_A["computed_at"])
    approve_plan(db_session, family, curator.id)

    # S1 = MED_URGENT, критично, дедлайн 2026-10-04 (computed_at + 3 дня).
    # +14 дней просрочки от дедлайна -> уровень 3.
    recompute_family(db_session, family, catalog, today=date(2026, 10, 20))

    plan = get_latest_plan(db_session, family.id)
    s1 = next(s for s in plan.plan_json["steps"] if s["step_id"] == "S1")
    assert s1["service_id"] == "MED_URGENT"
    assert s1["status"] == "overdue"
    assert s1["escalation_level"] == 3
