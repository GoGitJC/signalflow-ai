"""enforce one Retell agent maps to one business"""

from alembic import op

revision = "0003_voice_agent_unique"
down_revision = "0002_integrations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_voice_agents_retell_agent_id",
        "voice_agents",
        ["retell_agent_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_voice_agents_retell_agent_id", "voice_agents", type_="unique")
