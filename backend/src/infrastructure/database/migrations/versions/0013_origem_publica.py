"""origem da ocorrência, código de acompanhamento e usuário de sistema CIDADAO

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-05

- ``ocorrencias.origem`` (POLICIAL | PUBLICA): as linhas existentes ficam POLICIAL. As
  comunicações públicas antigas foram gravadas em nome do usuário ``agente`` e não há como
  distingui-las com segurança; continuam corrigíveis por ele, como antes.
- ``ocorrencias.codigo_acompanhamento_hash``: SHA-256 do código secreto entregue ao cidadão.
- Usuário ``sistema.cidadao`` (papel CIDADAO, inativo, sem senha utilizável): autor técnico
  das comunicações públicas no lugar do agente real.
"""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

TABELA = "ocorrencias"
LOGIN_SISTEMA = "sistema.cidadao"


def _colunas() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABELA)}


def upgrade() -> None:
    colunas = _colunas()
    with op.batch_alter_table(TABELA) as batch:
        if "origem" not in colunas:
            batch.add_column(sa.Column("origem", sa.String(20), nullable=False, server_default="POLICIAL"))
        if "codigo_acompanhamento_hash" not in colunas:
            batch.add_column(sa.Column("codigo_acompanhamento_hash", sa.String(64), nullable=True))

    usuarios = sa.table(
        "usuarios",
        sa.column("id", sa.Uuid()),
        sa.column("nome", sa.String()),
        sa.column("login", sa.String()),
        sa.column("senha_hash", sa.String()),
        sa.column("papel", sa.String()),
        sa.column("ativo", sa.Boolean()),
    )
    existe = op.get_bind().execute(sa.select(usuarios.c.id).where(usuarios.c.login == LOGIN_SISTEMA)).first()
    if existe is None:
        op.bulk_insert(
            usuarios,
            [
                {
                    "id": uuid.uuid4(),
                    "nome": "Delegacia Online (comunicação do cidadão)",
                    "login": LOGIN_SISTEMA,
                    "senha_hash": "!",
                    "papel": "CIDADAO",
                    "ativo": False,
                }
            ],
        )


def downgrade() -> None:
    # O usuário de sistema é mantido: ocorrências podem referenciá-lo (FK) e usuários não são apagados.
    colunas = _colunas()
    with op.batch_alter_table(TABELA) as batch:
        if "codigo_acompanhamento_hash" in colunas:
            batch.drop_column("codigo_acompanhamento_hash")
        if "origem" in colunas:
            batch.drop_column("origem")
