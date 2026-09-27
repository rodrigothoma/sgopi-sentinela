"""itens apreendidos e cadeia de custódia (RF03 / UC03)

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-20

- ``itens_apreendidos``: vínculo permanente à ocorrência; ``numero_lacre`` único em
  toda a base (UC03 exceção I). Nunca são apagados (RNF03*).
- ``movimentacoes_custodia``: eventos append-only (quem, quando, de onde, para onde),
  protegidos por trigger no PostgreSQL como o histórico de status.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

_TABELA_APPEND_ONLY = "movimentacoes_custodia"


def upgrade() -> None:
    op.create_table(
        "itens_apreendidos",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ocorrencia_id", sa.Uuid(), sa.ForeignKey("ocorrencias.id"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("unidade", sa.String(20), nullable=False, server_default="UNIDADE"),
        sa.Column("estado_conservacao", sa.String(20), nullable=False),
        sa.Column("numero_lacre", sa.String(60), nullable=False, unique=True),
        sa.Column("numero_serie", sa.String(100), nullable=True),
        sa.Column("marca", sa.String(100), nullable=True),
        sa.Column("calibre", sa.String(50), nullable=True),
        sa.Column("localizacao_deposito", sa.String(255), nullable=False),
        sa.Column("registrado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registrado_por_id", sa.Uuid(), sa.ForeignKey("usuarios.id"), nullable=False),
    )
    op.create_index("ix_itens_apreendidos_ocorrencia_id", "itens_apreendidos", ["ocorrencia_id"])
    op.create_index("ix_itens_apreendidos_numero_serie", "itens_apreendidos", ["numero_serie"])
    op.create_index("ix_itens_apreendidos_registrado_em", "itens_apreendidos", ["registrado_em"])

    op.create_table(
        _TABELA_APPEND_ONLY,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("item_id", sa.Uuid(), sa.ForeignKey("itens_apreendidos.id"), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("por_id", sa.Uuid(), nullable=False),
        sa.Column("origem", sa.String(255), nullable=True),
        sa.Column("destino", sa.String(255), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.UniqueConstraint("item_id", "ordem", name="uq_movimentacao_item_ordem"),
    )
    op.create_index("ix_movimentacoes_custodia_item_id", _TABELA_APPEND_ONLY, ["item_id"])

    if op.get_bind().dialect.name == "postgresql":
        # função sgopi_bloquear_alteracao() criada na migração 0001
        op.execute(
            f"CREATE TRIGGER trg_{_TABELA_APPEND_ONLY}_append_only BEFORE UPDATE OR DELETE ON {_TABELA_APPEND_ONLY} "
            "FOR EACH ROW EXECUTE FUNCTION sgopi_bloquear_alteracao();"
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute(f"DROP TRIGGER IF EXISTS trg_{_TABELA_APPEND_ONLY}_append_only ON {_TABELA_APPEND_ONLY};")
    op.drop_table(_TABELA_APPEND_ONLY)
    op.drop_table("itens_apreendidos")
