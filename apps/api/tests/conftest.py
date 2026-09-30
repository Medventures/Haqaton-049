import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import hash_password
from app.db import Base, get_db
from app.main import app
from app.models import Family, User


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    from fastapi.testclient import TestClient

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_curator(db_session, email="curator@demo.kz", name="Куратор"):
    user = User(role="curator", name=name, email=email, lang="ru", password_hash=hash_password("secret123"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def make_parent(db_session, email="parent@demo.kz", name="Родитель"):
    user = User(role="parent", name=name, email=email, lang="ru", password_hash=hash_password("secret123"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def make_family(db_session, curator, parent=None, child_name="Тест Тестов"):
    family = Family(child_name=child_name, curator_id=curator.id, parent_id=parent.id if parent else None)
    db_session.add(family)
    db_session.commit()
    db_session.refresh(family)
    return family


def login(client, email, password="secret123"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp
