"""evidências digitais vinculadas à ocorrência (RF22)

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-13
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidencias",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ocorrencia_id", sa.Uuid(), sa.ForeignKey("ocorrencias.id"), nullable=False),
        sa.Column("nome_original", sa.String(255), nullable=False),
        sa.Column("formato", sa.String(10), nullable=False),
        sa.Column("tamanho", sa.Integer(), nullable=False),
        sa.Column("hash_sha256", sa.String(64), nullable=False),
        sa.Column("chave_armazenamento", sa.String(255), nullable=False, unique=True),
        sa.Column("enviada_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evidencias_ocorrencia_id", "evidencias", ["ocorrencia_id"])
    op.create_index("ix_evidencias_hash_sha256", "evidencias", ["hash_sha256"])
    op.create_index("ix_evidencias_enviada_em", "evidencias", ["enviada_em"])


def downgrade() -> None:
    op.drop_table("evidencias")
