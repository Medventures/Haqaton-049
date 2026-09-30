"""Раздел 19 SPEC.md: движок строит план из profile_expected, без LLM."""
import json
from datetime import date

import pytest

from app.modules.engine.catalog import get_catalog
from app.modules.engine.engine import build_plan
from app.paths import FIXTURES_DIR


def _load_fixture(name):
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


CASE_A = _load_fixture("case_a.json")
CASE_B = _load_fixture("case_b.json")


def _steps_summary(steps):
    return [
        {
            "step_id": s["step_id"],
            "service_id": s["service_id"],
            "rule_id": s["rule_id"],
            "priority": s["priority"],
            "deadline": s["deadline"],
            "status": s["status"],
            "depends_on": s["depends_on"],
        }
        for s in steps
    ]


@pytest.mark.parametrize("fixture", [CASE_A, CASE_B], ids=["case_a", "case_b"])
def test_build_plan_matches_expected_steps(fixture):
    catalog = get_catalog()
    steps = build_plan(
        fixture["profile_expected"],
        catalog,
        date.fromisoformat(fixture["computed_at"]),
    )
    assert _steps_summary(steps) == fixture["expected_steps"]


@pytest.mark.parametrize("fixture", [CASE_A, CASE_B], ids=["case_a", "case_b"])
def test_build_plan_is_deterministic(fixture):
    catalog = get_catalog()
    computed_at = date.fromisoformat(fixture["computed_at"])
    first = build_plan(fixture["profile_expected"], catalog, computed_at)
    second = build_plan(fixture["profile_expected"], catalog, computed_at)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_case_b_step1_required_documents_in_wallet():
    catalog = get_catalog()
    steps = build_plan(
        CASE_B["profile_expected"], catalog, date.fromisoformat(CASE_B["computed_at"])
    )
    step1 = next(s for s in steps if s["step_id"] == "S1")
    assert step1["service_id"] == "EDU_PMPK_RENEW"
    required_docs = [d for d in step1["documents"] if d["kind"] == "required"]
    assert required_docs, "у EDU_PMPK_RENEW должны быть обязательные документы"
    assert all(d["in_wallet"] for d in required_docs)


def test_case_b_step1_deadline_compressed():
    catalog = get_catalog()
    steps = build_plan(
        CASE_B["profile_expected"], catalog, date.fromisoformat(CASE_B["computed_at"])
    )
    step1 = next(s for s in steps if s["step_id"] == "S1")
    assert step1["deadline_compressed"] is True


def test_unknown_service_id_rejected_by_catalog():
    catalog = get_catalog()
    assert "NOT_A_REAL_SERVICE" not in catalog.services


def test_plan_covers_at_least_two_agencies():
    # К4: в плане шаги минимум двух ведомств.
    catalog = get_catalog()
    for fixture in (CASE_A, CASE_B):
        steps = build_plan(
            fixture["profile_expected"], catalog, date.fromisoformat(fixture["computed_at"])
        )
        agencies = {s["agency"] for s in steps}
        assert len(agencies) >= 2, fixture["case_id"]
