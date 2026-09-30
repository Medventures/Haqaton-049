"""Раздел 13: /auth/invite -> /auth/register -> /auth/login.

Регрессия: SQLite возвращает DateTime(timezone=True) как naive после
round-trip через БД, из-за чего сравнение с aware datetime.now(timezone.utc)
падало с TypeError (найдено живым смоук-тестом, не было покрыто тестами
до этого — см. docs/DECISIONS.md).
"""
from tests.conftest import login, make_curator


def test_invite_register_login_flow(client, db_session):
    curator = make_curator(db_session)
    login(client, curator.email)

    resp = client.post("/api/auth/invite", json={"email": "parent.a@demo.kz", "child_name": "Тест"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["token"]

    client.post("/api/auth/logout")

    resp = client.post(
        "/api/auth/register",
        json={"token": token, "name": "Родитель", "password": "parent12345", "consent": True},
    )
    assert resp.status_code == 200, resp.text

    resp = client.post("/api/auth/login", json={"email": "parent.a@demo.kz", "password": "parent12345"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == "parent"


def test_register_rejects_used_invite(client, db_session):
    curator = make_curator(db_session)
    login(client, curator.email)
    token = client.post("/api/auth/invite", json={"email": "parent.b@demo.kz", "child_name": "Тест2"}).json()["token"]
    client.post("/api/auth/logout")

    body = {"token": token, "name": "Родитель2", "password": "parent12345", "consent": True}
    assert client.post("/api/auth/register", json=body).status_code == 200
    resp = client.post("/api/auth/register", json=body)
    assert resp.status_code == 422


def _signup(client, **overrides):
    body = {"name": "Айгуль", "email": "new.parent@example.kz", "password": "secret123", "child_name": "Арман", "consent": True}
    body.update(overrides)
    return client.post("/api/auth/signup", json=body)


def test_signup_creates_parent_family_and_session(client, db_session):
    from app.models import Family, User
    from tests.conftest import make_parent

    busy = make_curator(db_session, email="busy@demo.kz")
    free = make_curator(db_session, email="free@demo.kz")
    from tests.conftest import make_family

    make_family(db_session, busy, make_parent(db_session))

    resp = _signup(client, email="New.Parent@Example.kz")
    assert resp.status_code == 200, resp.text
    me = client.get("/api/auth/me").json()
    assert me["role"] == "parent" and me["email"] == "new.parent@example.kz"

    family = db_session.query(Family).filter(Family.parent_id == me["id"]).one()
    assert family.child_name == "Арман"
    assert family.curator_id == free.id  # куратор с наименьшим числом семей

    # Сразу можно начать интервью.
    assert client.post("/api/interview/start").status_code == 200

    client.post("/api/auth/logout")
    assert login(client, "NEW.PARENT@example.kz").status_code == 200
    assert db_session.query(User).filter(User.email == "new.parent@example.kz").count() == 1


def test_signup_validation(client, db_session):
    make_curator(db_session)
    assert _signup(client, consent=False).status_code == 422
    assert _signup(client, password="123").status_code == 422
    assert _signup(client, child_name="  ").status_code == 422
    assert _signup(client).status_code == 200
    client.post("/api/auth/logout")
    assert _signup(client).status_code == 409
