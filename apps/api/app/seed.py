"""Сид демо-аккаунтов и кейсов (раздел 19.5 SPEC.md).

Запуск: `python -m app.seed` (после `alembic upgrade head`).
Семья А создаётся без интервью, чтобы его можно было пройти на сцене.
Семья Б создаётся с пройденным интервью и подтверждённым планом
(кейс Б, раздел 19.2).
"""
import json
import sys
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import get_settings
from app.db import SessionLocal
from app.models import Family, Interview, User
from app.modules.engine.catalog import get_catalog
from app.modules.engine.engine import build_plan
from app.modules.llm.client import explain_step
from app.modules.plans.service import approve_plan, create_draft_plan
from app.paths import FIXTURES_DIR, REPO_ROOT


def _ensure_schema():
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(REPO_ROOT / "apps" / "api" / "alembic.ini"))
    command.upgrade(cfg, "head")


def seed(db: Session):
    settings = get_settings()
    if not settings.demo_password:
        raise SystemExit("DEMO_PASSWORD не задан в .env — задайте пароль для демо-аккаунтов перед сидом.")

    if db.query(User).filter_by(email="curator@demo.kz").first():
        print("Демо уже засеяно (curator@demo.kz существует). Ничего не делаю.")
        return

    password_hash = hash_password(settings.demo_password)
    curator = User(role="curator", name="Демо-куратор", email="curator@demo.kz", lang="ru", password_hash=password_hash)
    parent_a = User(role="parent", name="Родитель А", email="parent.a@demo.kz", lang="ru", password_hash=password_hash)
    parent_b = User(role="parent", name="Родитель Б", email="parent.b@demo.kz", lang="ru", password_hash=password_hash)
    db.add_all([curator, parent_a, parent_b])
    db.flush()

    family_a = Family(child_name="Демо-ребёнок А", region="karaganda_city", curator_id=curator.id, parent_id=parent_a.id)
    family_b = Family(child_name="Демо-ребёнок Б", region="karaganda_city", curator_id=curator.id, parent_id=parent_b.id)
    db.add_all([family_a, family_b])
    db.flush()
    # Семья А намеренно без Interview: интервью проходится вживую на сцене.

    with open(FIXTURES_DIR / "case_b.json", encoding="utf-8") as f:
        case_b = json.load(f)

    catalog = get_catalog()
    computed_at = date.fromisoformat(case_b["computed_at"])
    profile = case_b["profile_expected"]
    steps = build_plan(profile, catalog, computed_at)
    for step in steps:
        service = catalog.services[step["service_id"]]
        for lang in ("ru", "kk"):
            step[f"explanation_{lang}"] = explain_step(
                service, lang, needs_clarification=step["needs_clarification"], deadline_compressed=step["deadline_compressed"]
            )

    now = datetime.now(timezone.utc)
    answers = [
        {"question_id": qid, "value": value, "answered_at": now.isoformat()} for qid, value in case_b["answers"].items()
    ]
    interview_b = Interview(
        family_id=family_b.id,
        answers=answers,
        profile=profile,
        unknown_fields=profile["unknown_fields"],
        finished_at=now,
    )
    db.add(interview_b)
    db.flush()

    plan = create_draft_plan(db, family_b.id, steps, computed_at=case_b["computed_at"], profile_ref=f"I-{interview_b.id:03d}")
    db.commit()
    approve_plan(db, family_b, curator.id)

    print("Демо-данные созданы:")
    print("  curator@demo.kz / parent.a@demo.kz / parent.b@demo.kz — пароль из DEMO_PASSWORD")
    print(f"  Семья А (id={family_a.id}): без интервью — пройти на сцене.")
    print(f"  Семья Б (id={family_b.id}): интервью пройдено, план v{plan.version} подтверждён.")


def main():
    _ensure_schema()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
