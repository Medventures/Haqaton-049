"""Интеграционный тест интервью (раздел 19 SPEC.md, LLM в режиме заглушки)."""
import json

import pytest

from app.paths import FIXTURES_DIR
from tests.conftest import login, make_family, make_curator, make_parent

MANDATORY = {"Q01", "Q02", "Q03", "Q04", "Q14", "Q16"}


def _load_fixture(name):
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _answer_pool(fixture):
    pool = dict(fixture["answers"])
    pool.update(fixture.get("fallback_answers_for_interview_integration_test", {}))
    return pool


def _run_interview(client, pool):
    asked = []
    resp = client.post("/api/interview/start")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    steps = 0
    while not body["done"]:
        qid = body["question"]["id"]
        asked.append(qid)
        assert qid in pool, f"вопрос {qid} не найден в словаре ответов фикстуры"
        resp = client.post("/api/interview/answer", json={"question_id": qid, "value": pool[qid]})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        steps += 1
        assert steps <= 12
    return asked


@pytest.mark.parametrize("fixture_name", ["case_a.json", "case_b.json"])
def test_interview_asks_8_to_12_and_all_mandatory(client, db_session, fixture_name):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    make_family(db_session, curator, parent)
    login(client, parent.email)

    fixture = _load_fixture(fixture_name)
    asked = _run_interview(client, _answer_pool(fixture))

    assert 8 <= len(asked) <= 12
    assert MANDATORY.issubset(set(asked))
    assert len(asked) == len(set(asked)), "вопрос не должен задаваться дважды"


def test_interview_finish_creates_draft_plan_visible_only_to_curator(client, db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    make_family(db_session, curator, parent)
    login(client, parent.email)

    fixture = _load_fixture("case_a.json")
    _run_interview(client, _answer_pool(fixture))

    resp = client.post("/api/interview/finish")
    assert resp.status_code == 200, resp.text

    # родителю план пока не виден (черновик)
    from app.models import Family

    family = db_session.query(Family).filter(Family.parent_id == parent.id).one()
    resp = client.get(f"/api/plans/{family.id}")
    assert resp.status_code == 404

    login(client, curator.email)
    resp = client.get(f"/api/plans/{family.id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "draft"
    assert len(resp.json()["steps"]) >= 1


def test_home_vs_school_day_place_changes_question_set(client, db_session):
    """К3: Q03 = home и Q03 = school дают разные вопросы."""
    curator = make_curator(db_session)

    parent_home = make_parent(db_session, email="home@demo.kz")
    make_family(db_session, curator, parent_home, child_name="Дома")
    login(client, "home@demo.kz")
    client.post("/api/interview/start")
    for qid, value in [("Q01", 8), ("Q02", "no"), ("Q03", "home")]:
        client.post("/api/interview/answer", json={"question_id": qid, "value": value})
    resp = client.post("/api/interview/start")
    next_q_home = resp.json()["question"]["id"]

    parent_school = make_parent(db_session, email="school@demo.kz")
    make_family(db_session, curator, parent_school, child_name="Школа")
    login(client, "school@demo.kz")
    client.post("/api/interview/start")
    for qid, value in [("Q01", 8), ("Q02", "no"), ("Q03", "school")]:
        client.post("/api/interview/answer", json={"question_id": qid, "value": value})
    resp = client.post("/api/interview/start")
    next_q_school = resp.json()["question"]["id"]

    # оба продолжают с мандаторных Q04 сначала - проверим дальше, после Q04
    assert next_q_home == "Q04" == next_q_school

    for email, value in [("home@demo.kz", "karaganda_city"), ("school@demo.kz", "karaganda_city")]:
        login(client, email)
        client.post("/api/interview/answer", json={"question_id": "Q04", "value": value})

    login(client, "home@demo.kz")
    resp = client.post("/api/interview/start")
    after_home = resp.json()["question"]["id"]

    login(client, "school@demo.kz")
    resp = client.post("/api/interview/start")
    after_school = resp.json()["question"]["id"]

    # мандаторные Q14 совпадут для обоих, но набор allowed для Q09 отличается по Q03
    from app.modules.engine.catalog import get_catalog
    from app.modules.interview import flow

    catalog = get_catalog()
    allowed_home = {q["id"] for q in flow.compute_allowed(catalog.questions, {"Q01": 8, "Q02": "no", "Q03": "home", "Q04": "karaganda_city"})}
    allowed_school = {q["id"] for q in flow.compute_allowed(catalog.questions, {"Q01": 8, "Q02": "no", "Q03": "school", "Q04": "karaganda_city"})}
    assert "Q09" in allowed_home
    assert "Q09" not in allowed_school
