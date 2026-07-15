"""initial schema"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

user_role = postgresql.ENUM("owner", "admin", "member", name="userrole", create_type=False)
provider = postgresql.ENUM(
    "retell", "twilio", "calcom", name="integrationprovider", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    provider.create(bind, checkfirst=True)
    op.create_table(
        "businesses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("industry", sa.String(120)),
        sa.Column("phone_number", sa.String(32)),
        sa.Column("forwarding_number", sa.String(32)),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("business_hours", sa.JSON(), nullable=False),
        sa.Column("service_area", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "business_id",
            sa.String(36),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), unique=True, nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_business_id", "users", ["business_id"])
    op.create_table(
        "voice_agents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "business_id",
            sa.String(36),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("retell_agent_id", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("greeting", sa.Text(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("business_id", "retell_agent_id"),
    )
    op.create_index("ix_voice_agents_business_id", "voice_agents", ["business_id"])
    op.create_table(
        "knowledge_base_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "business_id",
            sa.String(36),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(120), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.create_index(
        "ix_knowledge_base_entries_business_id", "knowledge_base_entries", ["business_id"]
    )
    op.create_table(
        "callers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "business_id",
            sa.String(36),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200)),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("email", sa.String(320)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("business_id", "phone", name="uq_caller_business_phone"),
    )
    op.create_index("ix_callers_business_id", "callers", ["business_id"])
    op.create_table(
        "calls",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "business_id",
            sa.String(36),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("caller_id", sa.String(36), sa.ForeignKey("callers.id", ondelete="SET NULL")),
        sa.Column("retell_call_id", sa.String(200), nullable=False, unique=True),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("transcript", sa.Text()),
        sa.Column("summary", sa.Text()),
        sa.Column("intent", sa.String(120)),
        sa.Column("urgency", sa.String(40)),
        sa.Column("outcome", sa.String(80)),
        sa.Column("recording_url", sa.Text()),
        sa.Column("appointment_booked", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_calls_business_id", "calls", ["business_id"])
    op.create_index("ix_calls_caller_id", "calls", ["caller_id"])
    op.create_table(
        "appointments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "business_id",
            sa.String(36),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "caller_id",
            sa.String(36),
            sa.ForeignKey("callers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("call_id", sa.String(36), sa.ForeignKey("calls.id", ondelete="SET NULL")),
        sa.Column("cal_event_id", sa.String(200), unique=True),
        sa.Column("service", sa.String(200), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_appointments_business_id", "appointments", ["business_id"])
    op.create_index("ix_appointments_caller_id", "appointments", ["caller_id"])
    op.create_index("ix_appointments_call_id", "appointments", ["call_id"])
    op.create_table(
        "integrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "business_id",
            sa.String(36),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", provider, nullable=False),
        sa.Column("encrypted_credentials", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("business_id", "provider"),
    )
    op.create_index("ix_integrations_business_id", "integrations", ["business_id"])
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("event_key", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "event_key", name="uq_webhook_provider_key"),
    )
    op.create_index("ix_webhook_events_provider", "webhook_events", ["provider"])
    op.create_index("ix_webhook_events_event_key", "webhook_events", ["event_key"])


def downgrade() -> None:
    for table in [
        "webhook_events",
        "integrations",
        "appointments",
        "calls",
        "callers",
        "knowledge_base_entries",
        "voice_agents",
        "users",
        "businesses",
    ]:
        op.drop_table(table)
    provider.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
