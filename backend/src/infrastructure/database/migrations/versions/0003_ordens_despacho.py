"""ordens de despacho (RF02)

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-13
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ordens_despacho",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("numero", sa.String(30), nullable=False, unique=True),
        sa.Column("ocorrencia_id", sa.Uuid(), sa.ForeignKey("ocorrencias.id"), nullable=False),
        sa.Column("viatura_id", sa.Uuid(), sa.ForeignKey("viaturas.id"), nullable=False),
        sa.Column("operador_id", sa.Uuid(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("ativa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("encerrada_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ordens_despacho_ocorrencia_id", "ordens_despacho", ["ocorrencia_id"])
    op.create_index("ix_ordens_despacho_viatura_id", "ordens_despacho", ["viatura_id"])
    op.create_index("ix_ordens_despacho_criada_em", "ordens_despacho", ["criada_em"])
    op.create_index("ix_ordens_despacho_ativa", "ordens_despacho", ["ativa"])
    op.create_table(
        "sequencias_ordem_despacho",
        sa.Column("ano", sa.Integer(), primary_key=True),
        sa.Column("ultimo", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("sequencias_ordem_despacho")
    op.drop_table("ordens_despacho")
