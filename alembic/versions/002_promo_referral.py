"""promo codes and referral fields

Revision ID: 002_promo_referral
Revises: 001_initial
Create Date: 2026-04-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_promo_referral"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("referred_by_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("bonus_balance_days", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("first_payment_done", sa.Boolean(), server_default="false", nullable=False))
    op.create_foreign_key(
        "fk_users_referred_by_id",
        "users",
        "users",
        ["referred_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_users_referred_by_id"), "users", ["referred_by_id"], unique=False)

    op.create_table(
        "promo_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("bonus_days", sa.Integer(), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("uses_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_promo_codes_code"), "promo_codes", ["code"], unique=True)

    op.create_table(
        "promo_redemptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("promo_code_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["promo_code_id"], ["promo_codes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "promo_code_id", name="uq_promo_user_once"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO promo_codes (code, bonus_days, max_uses, uses_count, valid_until, active)
            SELECT 'WELCOME', 3, NULL, 0, NULL, true
            WHERE NOT EXISTS (SELECT 1 FROM promo_codes WHERE code = 'WELCOME')
            """
        )
    )


def downgrade() -> None:
    op.drop_table("promo_redemptions")
    op.drop_index(op.f("ix_promo_codes_code"), table_name="promo_codes")
    op.drop_table("promo_codes")
    op.drop_index(op.f("ix_users_referred_by_id"), table_name="users")
    op.drop_constraint("fk_users_referred_by_id", "users", type_="foreignkey")
    op.drop_column("users", "first_payment_done")
    op.drop_column("users", "bonus_balance_days")
    op.drop_column("users", "referred_by_id")
