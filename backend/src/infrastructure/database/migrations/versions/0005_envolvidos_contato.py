"""dados de contato do envolvido (email e telefone)
Revision ID: 0005
Revises: 0004
Create Date: 2026-09-19
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("envolvidos", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("envolvidos", sa.Column("telefone", sa.String(30), nullable=True))


def downgrade() -> None:
    op.drop_column("envolvidos", "telefone")
    op.drop_column("envolvidos", "email")
