from app import seed as seed_module
from app.models import CasePlan, Family, Interview, User


def test_seed_creates_demo_accounts_and_case_b_plan(db_session, monkeypatch):
    from app import config

    monkeypatch.setattr(config.get_settings(), "demo_password", "demo12345")

    seed_module.seed(db_session)

    emails = {u.email for u in db_session.query(User).all()}
    assert emails == {"curator@demo.kz", "parent.a@demo.kz", "parent.b@demo.kz"}

    families = db_session.query(Family).all()
    assert len(families) == 2

    family_a = next(f for f in families if f.child_name == "Демо-ребёнок А")
    family_b = next(f for f in families if f.child_name == "Демо-ребёнок Б")

    assert db_session.query(Interview).filter_by(family_id=family_a.id).count() == 0
    assert db_session.query(Interview).filter_by(family_id=family_b.id).count() == 1

    plan_b = (
        db_session.query(CasePlan)
        .filter_by(family_id=family_b.id)
        .order_by(CasePlan.version.desc())
        .first()
    )
    assert plan_b.status == "approved"
    assert {s["service_id"] for s in plan_b.plan_json["steps"]} == {
        "EDU_PMPK_RENEW",
        "EDU_ASSISTANT",
        "EDU_CHARACTERISTIC",
        "SOC_BENEFITS",
    }


def test_seed_is_idempotent(db_session, monkeypatch, capsys):
    from app import config

    monkeypatch.setattr(config.get_settings(), "demo_password", "demo12345")
    seed_module.seed(db_session)
    seed_module.seed(db_session)
    assert db_session.query(User).filter_by(email="curator@demo.kz").count() == 1
