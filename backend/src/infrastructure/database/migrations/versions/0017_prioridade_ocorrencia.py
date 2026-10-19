"""prioridade (gravidade) da ocorrência — sugestão #7

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-05

Acrescenta ``ocorrencias.prioridade`` (BAIXA | MEDIA | ALTA | URGENTE, padrão MEDIA) e preenche
as ocorrências existentes com a prioridade sugerida pela mesma regra do domínio (natureza +
tipificações). É uma coluna nova de dado operacional, não reescreve histórico nem auditoria.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from domain.ocorrencia.prioridade import sugerir_prioridade

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def _tem_coluna() -> bool:
    return "prioridade" in {c["name"] for c in sa.inspect(op.get_bind()).get_columns("ocorrencias")}


def _preencher_sugestoes() -> None:
    conexao = op.get_bind()
    tipificacoes: dict[str, list[str]] = {}
    for ocorrencia_id, artigo, descricao in conexao.execute(
        sa.text("SELECT ocorrencia_id, artigo, descricao FROM tipificacoes_ocorrencia WHERE ativo = :ativo"), {"ativo": True}
    ):
        tipificacoes.setdefault(str(ocorrencia_id), []).append(f"{artigo} {descricao}")
    for ocorrencia_id, natureza in conexao.execute(sa.text("SELECT id, natureza FROM ocorrencias")).all():
        prioridade = sugerir_prioridade(natureza, tipificacoes.get(str(ocorrencia_id), []))
        conexao.execute(
            sa.text("UPDATE ocorrencias SET prioridade = :p WHERE id = :id"), {"p": prioridade.value, "id": ocorrencia_id}
        )


def upgrade() -> None:
    if _tem_coluna():
        return
    with op.batch_alter_table("ocorrencias") as batch:
        batch.add_column(sa.Column("prioridade", sa.String(10), nullable=False, server_default="MEDIA"))
        batch.create_index("ix_ocorrencias_prioridade", ["prioridade"])
    _preencher_sugestoes()


def downgrade() -> None:
    if _tem_coluna():
        with op.batch_alter_table("ocorrencias") as batch:
            batch.drop_index("ix_ocorrencias_prioridade")
            batch.drop_column("prioridade")
