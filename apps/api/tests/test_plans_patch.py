"""Раздел 11.4: переходы статуса шага. Персистентность проверяется через
`expire_all()`, чтобы поймать регрессию "мутация вложенного словаря не
долетает до UPDATE" (см. docs/DECISIONS.md)."""
from app.modules.plans.service import create_draft_plan, get_latest_plan
from tests.conftest import login, make_curator, make_family, make_parent
from tests.test_api import SAMPLE_STEPS


def test_curator_marks_step_done_and_it_persists(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    steps = [dict(s, status="not_started") for s in SAMPLE_STEPS]
    create_draft_plan(db_session, family.id, steps, computed_at="2026-10-01")

    login(client, curator.email)
    resp = client.patch(f"/api/plans/{family.id}/steps/S1", json={"status": "in_progress"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["steps"][0]["status"] == "in_progress"

    db_session.expire_all()
    plan = get_latest_plan(db_session, family.id)
    assert plan.plan_json["steps"][0]["status"] == "in_progress"
    assert plan.plan_json["steps"][0]["status_history"], "status_history должен обновиться"


def test_parent_cannot_mark_step_done_for_education_org_step(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    steps = [dict(s, status="not_started", responsible="education_org") for s in SAMPLE_STEPS]
    create_draft_plan(db_session, family.id, steps, computed_at="2026-10-01")

    login(client, parent.email)
    resp = client.patch(f"/api/plans/{family.id}/steps/S1", json={"status": "done_by_parent"})
    assert resp.status_code == 409, resp.text


def test_invalid_transition_returns_409(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    steps = [dict(s, status="not_started") for s in SAMPLE_STEPS]
    create_draft_plan(db_session, family.id, steps, computed_at="2026-10-01")

    login(client, curator.email)
    resp = client.patch(f"/api/plans/{family.id}/steps/S1", json={"status": "done_by_parent"})
    assert resp.status_code == 403, resp.text
