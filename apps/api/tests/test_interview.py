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
    body = resp.json()
    assert body["status"] == "draft"
    assert len(body["steps"]) >= 1
    # К7 (раздел 20): у каждого шага есть объяснение на ru и kk.
    for step in body["steps"]:
        assert step["explanation_ru"], step["step_id"]
        assert step["explanation_kk"], step["step_id"]


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


def test_stale_question_is_rejected_and_start_resyncs(client, db_session):
    """Сайт показывает Q12 (зависит от Q10), а на сервере ответ Q10 уже
    отменён (другая вкладка, сброс демо-базы): ответ отвергается с 409, а
    /start возвращает актуальный вопрос и число ответов для восстановления."""
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    make_family(db_session, curator, parent)
    login(client, parent.email)

    pool = _answer_pool(_load_fixture("case_b.json"))
    body = client.post("/api/interview/start").json()
    assert body["answered"] == 0
    while body["question"]["id"] != "Q10":
        qid = body["question"]["id"]
        body = client.post("/api/interview/answer", json={"question_id": qid, "value": pool[qid]}).json()
    answered_before_q10 = body["answered"]
    client.post("/api/interview/answer", json={"question_id": "Q10", "value": "yes_with_ipr"})
    client.post("/api/interview/back")  # отменили Q10 «в другой вкладке»

    resp = client.post("/api/interview/answer", json={"question_id": "Q12", "value": ["none"]})
    assert resp.status_code == 409

    fresh = client.post("/api/interview/start").json()
    assert fresh["answered"] == answered_before_q10
    assert fresh["done"] is False


def test_unknown_dates_do_not_break_plan(client, db_session):
    """Ответ «Не знаю» на даты (Q07 срок ПМПК, Q11 переосвидетельствование)
    раньше ронял построение плана, а интервью оставалось завершённым без плана."""
    from app.models import CasePlan, Interview

    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    login(client, parent.email)

    pool = _answer_pool(_load_fixture("case_b.json"))
    pool.update({"Q07": "unknown", "Q10": "yes_with_ipr", "Q11": "unknown"})
    asked = _run_interview(client, pool)
    assert "Q11" in asked or "Q07" in asked

    resp = client.post("/api/interview/finish")
    assert resp.status_code == 200, resp.text
    assert db_session.query(CasePlan).filter(CasePlan.family_id == family.id).count() == 1
    assert db_session.query(Interview).filter(Interview.family_id == family.id).one().finished_at is not None


def test_finish_failure_keeps_interview_open(client, db_session, monkeypatch):
    from app.models import Interview
    from app.modules.interview import service

    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    login(client, parent.email)
    _run_interview(client, _answer_pool(_load_fixture("case_a.json")))

    def boom(*args, **kwargs):
        raise RuntimeError("engine failure")

    monkeypatch.setattr(service, "build_plan", boom)
    try:
        client.post("/api/interview/finish")
    except RuntimeError:
        pass
    db_session.expire_all()
    assert db_session.query(Interview).filter(Interview.family_id == family.id).one().finished_at is None

    monkeypatch.undo()
    assert client.post("/api/interview/finish").status_code == 200
