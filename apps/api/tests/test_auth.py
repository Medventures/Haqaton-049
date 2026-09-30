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
