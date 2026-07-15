"""integration metadata and audit trail"""

import sqlalchemy as sa

from alembic import op

revision = "0002_integrations"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("voice_agents", sa.Column("retell_agent_name", sa.String(200), nullable=True))
    op.add_column(
        "integrations",
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column("integrations", sa.Column("last_test_at", sa.DateTime(timezone=True)))
    op.add_column("integrations", sa.Column("last_test_status", sa.String(40)))
    op.add_column("integrations", sa.Column("last_test_error", sa.Text()))
    op.create_table(
        "integration_audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "business_id",
            sa.String(36),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("detail", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_integration_audit_events_business_id",
        "integration_audit_events",
        ["business_id"],
    )
    op.create_index(
        "ix_integration_audit_events_provider",
        "integration_audit_events",
        ["provider"],
    )


def downgrade() -> None:
    op.drop_index("ix_integration_audit_events_provider", table_name="integration_audit_events")
    op.drop_index("ix_integration_audit_events_business_id", table_name="integration_audit_events")
    op.drop_table("integration_audit_events")
    op.drop_column("integrations", "last_test_error")
    op.drop_column("integrations", "last_test_status")
    op.drop_column("integrations", "last_test_at")
    op.drop_column("integrations", "metadata_json")
    op.drop_column("voice_agents", "retell_agent_name")
