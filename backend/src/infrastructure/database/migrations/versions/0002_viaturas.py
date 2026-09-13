"""viaturas (RF15/RF16)

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-13
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "viaturas",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("prefixo", sa.String(20), nullable=False, unique=True),
        sa.Column("placa", sa.String(10), nullable=False, unique=True),
        sa.Column("situacao", sa.String(20), nullable=False, server_default="DISPONIVEL"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("posicao_registrada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("versao", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_viaturas_situacao", "viaturas", ["situacao"])


def downgrade() -> None:
    op.drop_table("viaturas")
