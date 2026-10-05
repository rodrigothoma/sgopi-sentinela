"""alinha índices e constraints UNIQUE ao modelo

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-05

A 0011 criou índices com nomes diferentes dos que o modelo declara (``index=True``), e as
0008/0011 deixaram no PostgreSQL constraints UNIQUE redundantes ao lado do índice único que o
modelo declara (``unique=True, index=True``). ``alembic check`` acusava a divergência; esta revisão a elimina para
que o próximo ``--autogenerate`` não misture essa correção com mudanças sem relação.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

TABELA = "comunicacoes_interagencias"
RENOMEACOES = (
    # (nome antigo da 0011, nome do modelo, coluna)
    ("ix_comunicacoes_interagencias_protocolo", "ix_comunicacoes_interagencias_protocolo_ocorrencia", "protocolo_ocorrencia"),
    ("ix_comunicacoes_interagencias_origem", "ix_comunicacoes_interagencias_departamento_origem", "departamento_origem"),
)
# (tabela, constraint UNIQUE redundante) — a unicidade continua garantida pelo índice único
UNIQUES_REDUNDANTES = (
    ("comunicacoes_interagencias", "comunicacoes_interagencias_numero_oficio_key"),
    ("inqueritos", "inqueritos_numero_key"),
    ("laudos_periciais", "laudos_periciais_numero_referencia_key"),
    ("medidas_protetivas", "medidas_protetivas_numero_referencia_key"),
)


def _indices() -> set[str]:
    return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(TABELA)}


def _uniques(tabela: str) -> set[str]:
    return {u["name"] for u in sa.inspect(op.get_bind()).get_unique_constraints(tabela) if u.get("name")}


def _trocar_indices(de_para: tuple[tuple[str, str, str], ...]) -> None:
    existentes = _indices()
    for antigo, novo, coluna in de_para:
        if antigo in existentes:
            op.drop_index(antigo, table_name=TABELA)
        if novo not in existentes:
            op.create_index(novo, TABELA, [coluna])


def upgrade() -> None:
    _trocar_indices(RENOMEACOES)
    if op.get_bind().dialect.name != "postgresql":
        return
    for tabela, constraint in UNIQUES_REDUNDANTES:
        if constraint in _uniques(tabela):
            op.drop_constraint(constraint, tabela, type_="unique")


def downgrade() -> None:
    _trocar_indices(tuple((novo, antigo, coluna) for antigo, novo, coluna in RENOMEACOES))
