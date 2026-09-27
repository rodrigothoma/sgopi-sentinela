"""arquivamento e exclusão lógica autorizados pelo Delegado, com motivo (RF20)

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-14

Idempotente / autocorretiva: um rascunho anterior desta migração usava o id de revisão
"0004" (o mesmo de ``0004_evidencias``) e chegou a ser aplicado em bancos de
desenvolvimento. Nesses bancos a ``alembic_version`` ficou em "0004" **sem** a tabela
``evidencias`` ter sido criada, e com as colunas de arquivamento já presentes. Por isso:
- a tabela ``evidencias`` (com seus índices) é criada aqui se não existir;
- cada coluna/constraint só é criada se ainda não existir;
- a coluna ``raio_area_metros`` (só existia no rascunho, nunca teve model) é removida.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

TABELA = "ocorrencias"
COLUNAS = (
    sa.Column("arquivada_por_id", sa.Uuid(), nullable=True),
    sa.Column("motivo_arquivamento", sa.Text(), nullable=True),
    sa.Column("excluida_por_id", sa.Uuid(), nullable=True),
    sa.Column("motivo_exclusao", sa.Text(), nullable=True),
)
FKS = {
    "fk_ocorrencias_arquivada_por_id_usuarios": "arquivada_por_id",
    "fk_ocorrencias_excluida_por_id_usuarios": "excluida_por_id",
}
COLUNA_RASCUNHO = "raio_area_metros"


def _estado_atual() -> tuple[set[str], set[str]]:
    inspector = sa.inspect(op.get_bind())
    colunas = {c["name"] for c in inspector.get_columns(TABELA)}
    fks = {fk["name"] for fk in inspector.get_foreign_keys(TABELA) if fk.get("name")}
    return colunas, fks


def _garantir_tabela_evidencias() -> None:
    """Réplica exata de ``0004_evidencias`` para bancos carimbados em 0004 pelo rascunho."""
    if sa.inspect(op.get_bind()).has_table("evidencias"):
        return
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


def upgrade() -> None:
    _garantir_tabela_evidencias()
    colunas, fks = _estado_atual()
    with op.batch_alter_table(TABELA) as batch:
        for coluna in COLUNAS:
            if coluna.name not in colunas:
                batch.add_column(coluna)
        for nome, coluna in FKS.items():
            if nome not in fks:
                batch.create_foreign_key(nome, "usuarios", [coluna], ["id"])
        if COLUNA_RASCUNHO in colunas:
            batch.drop_column(COLUNA_RASCUNHO)


def downgrade() -> None:
    colunas, fks = _estado_atual()
    with op.batch_alter_table(TABELA) as batch:
        for nome in FKS:
            if nome in fks:
                batch.drop_constraint(nome, type_="foreignkey")
        for coluna in reversed(COLUNAS):
            if coluna.name in colunas:
                batch.drop_column(coluna.name)
