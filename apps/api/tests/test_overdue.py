from datetime import date

from app.modules.engine.catalog import get_catalog
from app.modules.engine.engine import build_plan
from app.modules.plans.service import approve_plan, create_draft_plan
from app.modules.scheduler.escalation import recompute_family
from tests.conftest import login, make_curator, make_family, make_parent


def test_overdue_endpoint_lists_overdue_steps(client, db_session):
    catalog = get_catalog()
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)

    steps = build_plan({"child": {"age": 8}, "red_flags": ["regression"]}, catalog, date(2026, 10, 1))
    create_draft_plan(db_session, family.id, steps, computed_at="2026-10-01")
    approve_plan(db_session, family, curator.id)
    recompute_family(db_session, family, catalog, today=date(2026, 10, 20))

    login(client, curator.email)
    resp = client.get("/api/overdue")
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert any(r["family_id"] == family.id for r in rows)
