"""no máximo uma ordem de despacho ativa por viatura

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-05

Índice único parcial ``(viatura_id) WHERE ativa``: dois despachos concorrentes da mesma viatura
não conseguem gravar duas ordens ativas (antes só a checagem em memória de ``despachavel``
os separava). Se a base já tiver duplicidades, a migração falha com mensagem explícita.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

INDICE = "uq_ordens_despacho_viatura_ativa"
TABELA = "ordens_despacho"


def upgrade() -> None:
    if INDICE in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(TABELA)}:
        return
    duplicadas = op.get_bind().execute(
        sa.text(f"SELECT viatura_id FROM {TABELA} WHERE ativa GROUP BY viatura_id HAVING COUNT(*) > 1")
    ).fetchall()
    if duplicadas:
        raise RuntimeError(
            f"Viaturas com mais de uma ordem ativa: {[str(d[0]) for d in duplicadas]}. "
            "Encerre as ordens excedentes antes de aplicar a 0015."
        )
    op.create_index(
        INDICE, TABELA, ["viatura_id"], unique=True,
        postgresql_where=sa.text("ativa"), sqlite_where=sa.text("ativa"),
    )


def downgrade() -> None:
    if INDICE in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(TABELA)}:
        op.drop_index(INDICE, table_name=TABELA)
