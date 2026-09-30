from app.modules.plans.service import approve_plan, create_draft_plan
from tests.conftest import login, make_curator, make_family, make_parent

SAMPLE_STEPS = [
    {
        "step_id": "S1",
        "service_id": "MED_URGENT",
        "title_ru": "Срочная консультация врача",
        "title_kk": "Дәрігердің шұғыл кеңесі",
        "agency": "medicine",
        "responsible": "parent",
        "priority": "critical",
        "depends_on": [],
        "start_date": "2026-10-01",
        "deadline": "2026-10-04",
        "original_deadline": "2026-10-04",
        "documents": [],
        "status": "not_started",
        "explanation_ru": "...",
        "explanation_kk": "...",
        "rule_id": "R01",
        "source_ids": [],
        "provider_ids": [],
        "added_by": "engine",
        "needs_clarification": False,
        "deadline_compressed": False,
        "escalation_level": 0,
        "status_history": [],
    }
]


def test_add_step_with_unknown_service_id_returns_422(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    create_draft_plan(db_session, family.id, list(SAMPLE_STEPS), computed_at="2026-10-01")

    login(client, curator.email)
    resp = client.post(f"/api/plans/{family.id}/steps", json={"service_id": "NOT_A_REAL_SERVICE"})
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "invalid_request"


def test_add_step_with_real_service_id_succeeds(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    create_draft_plan(db_session, family.id, list(SAMPLE_STEPS), computed_at="2026-10-01")

    login(client, curator.email)
    resp = client.post(f"/api/plans/{family.id}/steps", json={"service_id": "EDU_KPPK"})
    assert resp.status_code == 200, resp.text
    service_ids = [s["service_id"] for s in resp.json()["steps"]]
    assert "EDU_KPPK" in service_ids


def test_parent_cannot_see_draft_plan(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    create_draft_plan(db_session, family.id, list(SAMPLE_STEPS), computed_at="2026-10-01")

    login(client, parent.email)
    resp = client.get(f"/api/plans/{family.id}")
    assert resp.status_code == 404, resp.text
    assert resp.json()["error"]["code"] == "not_found"


def test_parent_without_plan_gets_no_plan_code(client, db_session):
    # Web по коду no_plan отправляет родителя на интервью, а не на экран
    # ожидания куратора.
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)

    login(client, parent.email)
    resp = client.get(f"/api/plans/{family.id}")
    assert resp.status_code == 404, resp.text
    assert resp.json()["error"]["code"] == "no_plan"


def test_parent_sees_plan_once_approved(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    create_draft_plan(db_session, family.id, list(SAMPLE_STEPS), computed_at="2026-10-01")
    approve_plan(db_session, family, curator.id)

    login(client, parent.email)
    resp = client.get(f"/api/plans/{family.id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "approved"


def test_parent_cannot_access_another_familys_plan(client, db_session):
    curator = make_curator(db_session)
    parent_a = make_parent(db_session, email="parent.a@demo.kz")
    parent_b = make_parent(db_session, email="parent.b@demo.kz")
    family_a = make_family(db_session, curator, parent_a, child_name="Ребёнок А")
    family_b = make_family(db_session, curator, parent_b, child_name="Ребёнок Б")
    create_draft_plan(db_session, family_a.id, list(SAMPLE_STEPS), computed_at="2026-10-01")
    create_draft_plan(db_session, family_b.id, list(SAMPLE_STEPS), computed_at="2026-10-01")
    approve_plan(db_session, family_a, curator.id)
    approve_plan(db_session, family_b, curator.id)

    login(client, parent_a.email)
    resp = client.get(f"/api/plans/{family_b.id}")
    assert resp.status_code == 404, resp.text


def test_curator_cannot_access_another_curators_family(client, db_session):
    curator_a = make_curator(db_session, email="curator.a@demo.kz")
    curator_b = make_curator(db_session, email="curator.b@demo.kz")
    parent = make_parent(db_session)
    family = make_family(db_session, curator_a, parent)
    create_draft_plan(db_session, family.id, list(SAMPLE_STEPS), computed_at="2026-10-01")

    login(client, curator_b.email)
    resp = client.get(f"/api/plans/{family.id}")
    assert resp.status_code == 404, resp.text


def test_unauthenticated_request_is_rejected(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    resp = client.get(f"/api/plans/{family.id}")
    assert resp.status_code == 401, resp.text


def test_approve_requires_draft(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    create_draft_plan(db_session, family.id, list(SAMPLE_STEPS), computed_at="2026-10-01")
    approve_plan(db_session, family, curator.id)

    login(client, curator.email)
    resp = client.post(f"/api/plans/{family.id}/approve")
    assert resp.status_code == 409, resp.text


def test_delete_step_only_in_draft(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    create_draft_plan(db_session, family.id, list(SAMPLE_STEPS), computed_at="2026-10-01")
    approve_plan(db_session, family, curator.id)

    login(client, curator.email)
    resp = client.delete(f"/api/plans/{family.id}/steps/S1")
    assert resp.status_code == 409, resp.text
