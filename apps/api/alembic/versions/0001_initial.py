"""initial schema (SPEC.md, раздел 14)

Revision ID: 0001
Revises:
Create Date: 2026-09-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("lang", sa.String(2), nullable=False, server_default="ru"),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "families",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("child_name", sa.String(255), nullable=False),
        sa.Column("child_birth_date", sa.String(10), nullable=True),
        sa.Column("region", sa.String(32), nullable=True),
        sa.Column("curator_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "invites",
        sa.Column("token", sa.String(64), primary_key=True),
        sa.Column("family_id", sa.Integer, sa.ForeignKey("families.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("family_id", sa.Integer, sa.ForeignKey("families.id"), nullable=False),
        sa.Column("answers", sa.JSON, nullable=False),
        sa.Column("profile", sa.JSON, nullable=False),
        sa.Column("unknown_fields", sa.JSON, nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_interviews_family_id", "interviews", ["family_id"])

    op.create_table(
        "clarifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("family_id", sa.Integer, sa.ForeignKey("families.id"), nullable=False),
        sa.Column("question_id", sa.String(8), nullable=False),
        sa.Column("asked_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("asked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_clarifications_family_id", "clarifications", ["family_id"])

    op.create_table(
        "case_plans",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("family_id", sa.Integer, sa.ForeignKey("families.id"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("plan_json", sa.JSON, nullable=False),
        sa.Column("created_by", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("family_id", "version", name="uq_case_plans_family_version"),
    )
    op.create_index("ix_case_plans_family_id", "case_plans", ["family_id"])

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("family_id", sa.Integer, sa.ForeignKey("families.id"), nullable=False),
        sa.Column("doc_type", sa.String(32), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("issued_at", sa.String(10), nullable=True),
        sa.Column("valid_until", sa.String(10), nullable=True),
        sa.Column("issuer", sa.String(255), nullable=True),
        sa.Column("confirmed_by_parent", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("verified_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_family_id", "documents", ["family_id"])

    op.create_table(
        "escalations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("family_id", sa.Integer, sa.ForeignKey("families.id"), nullable=False),
        sa.Column("step_id", sa.String(16), nullable=False),
        sa.Column("level", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("appeal_text", sa.String, nullable=True),
    )
    op.create_index("ix_escalations_family_id", "escalations", ["family_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("channels", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "outbox",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("to_email", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("family_id", sa.Integer, sa.ForeignKey("families.id"), nullable=False),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("before", sa.JSON, nullable=True),
        sa.Column("after", sa.JSON, nullable=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_log_family_id", "audit_log", ["family_id"])

    op.create_table(
        "llm_cache",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("call_type", sa.String(32), nullable=False),
        sa.Column("response", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "filter_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("call_type", sa.String(32), nullable=False),
        sa.Column("service_id", sa.String(32), nullable=True),
        sa.Column("pattern", sa.String(255), nullable=False),
        sa.Column("attempt", sa.Integer, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.String, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("filter_events")
    op.drop_table("llm_cache")
    op.drop_table("audit_log")
    op.drop_table("outbox")
    op.drop_table("notifications")
    op.drop_table("escalations")
    op.drop_table("documents")
    op.drop_table("case_plans")
    op.drop_table("clarifications")
    op.drop_table("interviews")
    op.drop_table("invites")
    op.drop_table("families")
    op.drop_table("users")
