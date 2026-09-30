"""Модель данных (раздел 14 SPEC.md).

Справочники из data/ в БД не копируются — API загружает их в память при
старте (см. app/modules/engine/catalog.py).
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String(16))  # parent | curator
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lang: Mapped[str] = mapped_column(String(2), default="ru")
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Family(Base):
    __tablename__ = "families"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    child_name: Mapped[str] = mapped_column(String(255))
    child_birth_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    region: Mapped[str | None] = mapped_column(String(32), nullable=True)
    curator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    curator: Mapped["User | None"] = relationship(foreign_keys=[curator_id])
    parent: Mapped["User | None"] = relationship(foreign_keys=[parent_id])


class Invite(Base):
    __tablename__ = "invites"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"))
    email: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    answers: Mapped[list] = mapped_column(JSON, default=list)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    unknown_fields: Mapped[list] = mapped_column(JSON, default=list)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Clarification(Base):
    __tablename__ = "clarifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    question_id: Mapped[str] = mapped_column(String(8))
    asked_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CasePlan(Base):
    __tablename__ = "case_plans"
    __table_args__ = (UniqueConstraint("family_id", "version", name="uq_case_plans_family_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16))  # draft | approved | archived
    plan_json: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[str] = mapped_column(String(16))  # engine | curator
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    doc_type: Mapped[str] = mapped_column(String(32))
    file_path: Mapped[str] = mapped_column(String(1024))
    issued_at: Mapped[str | None] = mapped_column(String(10), nullable=True)
    valid_until: Mapped[str | None] = mapped_column(String(10), nullable=True)
    issuer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confirmed_by_parent: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    step_id: Mapped[str] = mapped_column(String(16))
    level: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    appeal_text: Mapped[str | None] = mapped_column(String, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    channels: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Outbox(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    to_email: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class LlmCache(Base):
    __tablename__ = "llm_cache"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    call_type: Mapped[str] = mapped_column(String(32))
    response: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class FilterEvent(Base):
    __tablename__ = "filter_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_type: Mapped[str] = mapped_column(String(32))
    service_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pattern: Mapped[str] = mapped_column(String(255))
    attempt: Mapped[int] = mapped_column(Integer)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str | None] = mapped_column(String, nullable=True)
