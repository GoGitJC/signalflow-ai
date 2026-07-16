"""auth audit events foundation"""

import sqlalchemy as sa

from alembic import op

revision = "0005_auth_audit_events"
down_revision = "0004_auth_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("business_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_auth_audit_events_business_id", "auth_audit_events", ["business_id"])
    op.create_index("ix_auth_audit_events_action", "auth_audit_events", ["action"])


def downgrade() -> None:
    op.drop_index("ix_auth_audit_events_action", table_name="auth_audit_events")
    op.drop_index("ix_auth_audit_events_business_id", table_name="auth_audit_events")
    op.drop_table("auth_audit_events")
