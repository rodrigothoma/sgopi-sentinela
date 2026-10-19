"""leitura de notificação por usuário

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-05

O flag ``notificacoes.lida`` era único por linha: um usuário marcava como lida, para o papel
inteiro, uma notificação de papel ou de difusão. A leitura passa a ser registrada por usuário
em ``notificacoes_leituras``. As leituras de notificações **pessoais** são migradas; as de papel
e difusão não têm autor identificável e voltam a aparecer como pendentes. A coluna antiga fica
sem uso (sem DROP: dados de negócio não são apagados).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

TABELA = "notificacoes_leituras"


def upgrade() -> None:
    if TABELA in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        TABELA,
        sa.Column("notificacao_id", sa.Uuid(), sa.ForeignKey("notificacoes.id"), primary_key=True),
        sa.Column("usuario_id", sa.Uuid(), sa.ForeignKey("usuarios.id"), primary_key=True),
        sa.Column("lida_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        f"INSERT INTO {TABELA} (notificacao_id, usuario_id, lida_em) "
        "SELECT id, usuario_id, COALESCE(lida_em, criada_em) FROM notificacoes "
        "WHERE lida = true AND usuario_id IS NOT NULL"
    )


def downgrade() -> None:
    if TABELA in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table(TABELA)
