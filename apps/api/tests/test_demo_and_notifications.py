from app.modules.plans.service import create_draft_plan
from tests.conftest import login, make_curator, make_family, make_parent
from tests.test_api import SAMPLE_STEPS


def test_demo_endpoints_require_demo_mode(client, db_session, monkeypatch):
    curator = make_curator(db_session)
    login(client, curator.email)
    resp = client.post("/api/demo/time-shift", json={"offset_days": 10})
    assert resp.status_code == 403
    assert client.get("/api/demo/state").status_code == 403


def test_demo_time_shift_and_dev_mail(client, db_session, monkeypatch):
    from app import config

    monkeypatch.setattr(config.get_settings(), "demo_mode", True)
    curator = make_curator(db_session)
    login(client, curator.email)

    resp = client.post("/api/demo/time-shift", json={"offset_days": 15})
    assert resp.status_code == 200, resp.text
    assert resp.json()["time_offset_days"] == 15

    state = client.get("/api/demo/state").json()
    assert state["time_offset_days"] == 15
    assert state["today"] == resp.json()["today"]

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


def test_demo_quick_login(client, db_session, monkeypatch):
    from app import config

    parent = make_parent(db_session, email="parent.a@demo.kz", name="Родитель А")
    make_curator(db_session)

    assert client.get("/api/demo/accounts").status_code == 403
    assert client.post("/api/demo/login", json={"key": "parent_a"}).status_code == 403

    monkeypatch.setattr(config.get_settings(), "demo_mode", True)
    accounts = client.get("/api/demo/accounts").json()
    assert {a["key"] for a in accounts} == {"parent_a", "curator"}

    resp = client.post("/api/demo/login", json={"key": "parent_a"})
    assert resp.status_code == 200, resp.text
    assert client.get("/api/auth/me").json()["id"] == parent.id

    # Только демо-аккаунты, произвольный email не пускает.
    assert client.post("/api/demo/login", json={"key": "someone@else.kz"}).status_code == 404
    assert client.post("/api/demo/login", json={"key": "parent_b"}).status_code == 404
