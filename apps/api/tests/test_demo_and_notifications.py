from app.modules.plans.service import create_draft_plan
from tests.conftest import login, make_curator, make_family, make_parent
from tests.test_api import SAMPLE_STEPS


def test_demo_endpoints_require_demo_mode(client, db_session, monkeypatch):
    curator = make_curator(db_session)
    login(client, curator.email)
    resp = client.post("/api/demo/time-shift", json={"offset_days": 10})
    assert resp.status_code == 403


def test_demo_time_shift_and_dev_mail(client, db_session, monkeypatch):
    from app import config

    monkeypatch.setattr(config.get_settings(), "demo_mode", True)
    curator = make_curator(db_session)
    login(client, curator.email)

    resp = client.post("/api/demo/time-shift", json={"offset_days": 15})
    assert resp.status_code == 200, resp.text
    assert resp.json()["time_offset_days"] == 15

    resp = client.get("/api/dev/mail")
    assert resp.status_code == 200

    resp = client.post("/api/demo/reset")
    assert resp.status_code == 200


def test_notifications_center_flow(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    create_draft_plan(db_session, family.id, list(SAMPLE_STEPS), computed_at="2026-10-01")

    from app.modules.plans.service import approve_plan

    approve_plan(db_session, family, curator.id)

    login(client, parent.email)
    resp = client.get("/api/notifications")
    assert resp.status_code == 200
    items = resp.json()
    assert any(n["type"] == "plan_approved" for n in items)

    ids = [n["id"] for n in items]
    resp = client.post("/api/notifications/read", json={"ids": ids})
    assert resp.status_code == 200
    assert resp.json()["updated"] == len(ids)
