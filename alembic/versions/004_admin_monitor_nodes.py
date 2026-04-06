"""admin monitor nodes table (CRUD from dashboard)

Revision ID: 004_admin_monitor_nodes
Revises: 003_public_sub_token
Create Date: 2026-04-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_admin_monitor_nodes"
down_revision: Union[str, None] = "003_public_sub_token"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_monitor_nodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("node_key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("instance", sa.String(length=256), nullable=False),
        sa.Column("panel_health_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("node_key"),
    )


def downgrade() -> None:
    op.drop_table("admin_monitor_nodes")
