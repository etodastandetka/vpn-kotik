"""user public subscription token for /sub/{token}

Revision ID: 003_public_sub_token
Revises: 002_promo_referral
Create Date: 2026-04-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_public_sub_token"
down_revision: Union[str, None] = "002_promo_referral"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("public_sub_token", sa.String(length=64), nullable=True))
    op.create_index("ix_users_public_sub_token", "users", ["public_sub_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_public_sub_token", table_name="users")
    op.drop_column("users", "public_sub_token")
