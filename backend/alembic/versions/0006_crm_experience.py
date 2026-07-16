"""CRM experience: callers, sentiment, voice agent, KB versions"""

import sqlalchemy as sa

from alembic import op

revision = "0006_crm_experience"
down_revision = "0005_auth_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("callers", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "callers", sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
    )
    op.add_column(
        "callers",
        sa.Column("status", sa.String(length=40), nullable=False, server_default="lead"),
    )
    op.add_column("callers", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("calls", sa.Column("sentiment", sa.String(length=40), nullable=True))

    op.add_column("voice_agents", sa.Column("voice", sa.String(length=80), nullable=True))
    op.add_column("voice_agents", sa.Column("temperature", sa.Float(), nullable=True))
    op.add_column("voice_agents", sa.Column("transfer_number", sa.String(length=32), nullable=True))
    op.add_column("voice_agents", sa.Column("transfer_rules", sa.Text(), nullable=True))
    op.add_column(
        "voice_agents",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "knowledge_base_entries",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "knowledge_base_entries",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "knowledge_base_entry_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("entry_id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["entry_id"], ["knowledge_base_entries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_kb_entry_versions_entry_id", "knowledge_base_entry_versions", ["entry_id"])
    op.create_index(
        "ix_kb_entry_versions_business_id", "knowledge_base_entry_versions", ["business_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_kb_entry_versions_business_id", table_name="knowledge_base_entry_versions")
    op.drop_index("ix_kb_entry_versions_entry_id", table_name="knowledge_base_entry_versions")
    op.drop_table("knowledge_base_entry_versions")
    op.drop_column("knowledge_base_entries", "created_at")
    op.drop_column("knowledge_base_entries", "updated_at")
    op.drop_column("voice_agents", "updated_at")
    op.drop_column("voice_agents", "transfer_rules")
    op.drop_column("voice_agents", "transfer_number")
    op.drop_column("voice_agents", "temperature")
    op.drop_column("voice_agents", "voice")
    op.drop_column("calls", "sentiment")
    op.drop_column("callers", "updated_at")
    op.drop_column("callers", "status")
    op.drop_column("callers", "tags")
    op.drop_column("callers", "notes")
