"""ordem de despacho: viatura de apoio

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-28

- ``ordens_despacho.apoio``: booleano; ``False`` = viatura principal (primeiro
  despacho), ``True`` = viatura de apoio despachada com a ocorrência já
  EM_ATENDIMENTO. Ordemas existentes permanecem ``False`` por ``server_default``.
- Idempotente: a coluna só é criada se ainda não existir (PostgreSQL e SQLite).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

TABELA = "ordens_despacho"
COLUNA = "apoio"


def _coluna_existe() -> bool:
    return COLUNA in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABELA)}


def upgrade() -> None:
    if not _coluna_existe():
        op.add_column(TABELA, sa.Column(COLUNA, sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    if _coluna_existe():
        op.drop_column(TABELA, COLUNA)
