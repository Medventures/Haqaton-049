"""Раздел 17: все три PDF-отчёта генерируются на обоих языках."""
import pytest

from app.modules.plans.service import approve_plan, create_draft_plan
from tests.conftest import login, make_curator, make_family, make_parent
from tests.test_api import SAMPLE_STEPS


@pytest.fixture()
def approved_family(db_session):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)
    create_draft_plan(db_session, family.id, list(SAMPLE_STEPS), computed_at="2026-10-01")
    approve_plan(db_session, family, curator.id)
    return curator, parent, family


@pytest.mark.parametrize("lang", ["ru", "kk"])
def test_route_report_both_languages(client, db_session, approved_family, lang):
    curator, parent, family = approved_family
    login(client, curator.email)
    resp = client.get(f"/api/reports/route/{family.id}.pdf", params={"lang": lang})
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"


@pytest.mark.parametrize("lang", ["ru", "kk"])
def test_visit_report_both_languages(client, db_session, approved_family, lang):
    curator, parent, family = approved_family
    login(client, parent.email)
    resp = client.get(f"/api/reports/visit/{family.id}.pdf", params={"lang": lang, "step": "S1"})
    assert resp.status_code == 200, resp.text
    assert resp.content[:4] == b"%PDF"


@pytest.mark.parametrize("lang", ["ru", "kk"])
def test_summary_report_both_languages(client, db_session, approved_family, lang):
    curator, parent, family = approved_family
    login(client, curator.email)
    resp = client.get(f"/api/reports/summary/{family.id}.pdf", params={"lang": lang})
    assert resp.status_code == 200, resp.text
    assert resp.content[:4] == b"%PDF"
