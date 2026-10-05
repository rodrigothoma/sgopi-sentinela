"""versão do algoritmo do hash_narrativa

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-05

A canonicalização v1 do ``hash_narrativa`` (junção por "\\n" e "|") é ambígua; a v2 usa JSON
canônico e inclui o SHA-256 das evidências. ``hash_versao`` registra com qual algoritmo cada
documento foi emitido: os já validados ficam com 1 e continuam verificáveis.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "hash_versao" in {c["name"] for c in sa.inspect(op.get_bind()).get_columns("ocorrencias")}:
        return
    with op.batch_alter_table("ocorrencias") as batch:
        batch.add_column(sa.Column("hash_versao", sa.Integer(), nullable=True))
    op.execute("UPDATE ocorrencias SET hash_versao = 1 WHERE hash_narrativa IS NOT NULL")


def downgrade() -> None:
    if "hash_versao" in {c["name"] for c in sa.inspect(op.get_bind()).get_columns("ocorrencias")}:
        with op.batch_alter_table("ocorrencias") as batch:
            batch.drop_column("hash_versao")
