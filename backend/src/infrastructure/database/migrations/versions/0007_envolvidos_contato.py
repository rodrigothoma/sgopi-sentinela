"""dados de contato do envolvido (email e telefone)

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-19

Idempotente: esta migração nasceu em outra branch com o id "0005" (colidindo com
``0005_arquivamento_exclusao``) e pode já ter sido aplicada em bancos de
desenvolvimento sob aquele id. Cada coluna só é criada/removida se necessário.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

TABELA = "envolvidos"
COLUNAS = (
    sa.Column("email", sa.String(255), nullable=True),
    sa.Column("telefone", sa.String(30), nullable=True),
)


def _colunas_atuais() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABELA)}


def upgrade() -> None:
    existentes = _colunas_atuais()
    for coluna in COLUNAS:
        if coluna.name not in existentes:
            op.add_column(TABELA, coluna)


def downgrade() -> None:
    existentes = _colunas_atuais()
    for coluna in reversed(COLUNAS):
        if coluna.name in existentes:
            op.drop_column(TABELA, coluna.name)
