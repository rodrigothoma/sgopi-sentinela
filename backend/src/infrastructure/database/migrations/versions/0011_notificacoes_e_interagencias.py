"""notificacoes, comunicacoes_interagencias e sequencias_oficio

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-03
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def _coluna_existe(tabela: str, coluna: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return coluna in {c["name"] for c in insp.get_columns(tabela)}


def _tabela_existe(tabela: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return tabela in insp.get_table_names()


def upgrade() -> None:
    # 1. Tabela notificacoes (RF05, RF09, RF10)
    if not _tabela_existe("notificacoes"):
        op.create_table(
            "notificacoes",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("usuario_id", sa.Uuid(), sa.ForeignKey("usuarios.id"), nullable=True),
            sa.Column("papel_destinatario", sa.String(30), nullable=True),
            sa.Column("departamento_destinatario", sa.String(50), nullable=True),
            sa.Column("tipo", sa.String(40), nullable=False),
            sa.Column("titulo", sa.String(255), nullable=False),
            sa.Column("mensagem", sa.Text(), nullable=False),
            sa.Column("prioridade", sa.String(20), nullable=False, server_default="MEDIA"),
            sa.Column("link", sa.String(255), nullable=True),
            sa.Column("lida", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("lida_em", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadados", sa.JSON(), nullable=True),
            sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.create_index("ix_notificacoes_usuario_id", "notificacoes", ["usuario_id"])
        op.create_index("ix_notificacoes_papel_destinatario", "notificacoes", ["papel_destinatario"])
        op.create_index("ix_notificacoes_departamento_destinatario", "notificacoes", ["departamento_destinatario"])
        op.create_index("ix_notificacoes_tipo", "notificacoes", ["tipo"])
        op.create_index("ix_notificacoes_lida", "notificacoes", ["lida"])
        op.create_index("ix_notificacoes_criada_em", "notificacoes", ["criada_em"])

    # 2. Tabela comunicacoes_interagencias (RF10 / UC10)
    if not _tabela_existe("comunicacoes_interagencias"):
        op.create_table(
            "comunicacoes_interagencias",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("numero_oficio", sa.String(50), nullable=False, unique=True),
            sa.Column("protocolo_ocorrencia", sa.String(50), nullable=True),
            sa.Column("departamento_origem", sa.String(50), nullable=False),
            sa.Column("departamentos_destinatarios", sa.JSON(), nullable=False),
            sa.Column("remetente_id", sa.Uuid(), sa.ForeignKey("usuarios.id"), nullable=False),
            sa.Column("assunto", sa.String(255), nullable=False),
            sa.Column("corpo", sa.Text(), nullable=False),
            sa.Column("nivel_sigilo", sa.String(30), nullable=False, server_default="PADRAO"),
            sa.Column("prioridade", sa.String(20), nullable=False, server_default="MEDIA"),
            sa.Column("status_entrega", sa.String(30), nullable=False, server_default="ENTREGUE"),
            sa.Column("mensagem_pai_id", sa.Uuid(), sa.ForeignKey("comunicacoes_interagencias.id"), nullable=True),
            sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.create_index("ix_comunicacoes_interagencias_numero_oficio", "comunicacoes_interagencias", ["numero_oficio"], unique=True)
        op.create_index("ix_comunicacoes_interagencias_protocolo", "comunicacoes_interagencias", ["protocolo_ocorrencia"])
        op.create_index("ix_comunicacoes_interagencias_origem", "comunicacoes_interagencias", ["departamento_origem"])
        op.create_index("ix_comunicacoes_interagencias_criada_em", "comunicacoes_interagencias", ["criada_em"])

    # 3. Tabela sequencias_oficio
    if not _tabela_existe("sequencias_oficio"):
        op.create_table(
            "sequencias_oficio",
            sa.Column("ano", sa.Integer(), primary_key=True),
            sa.Column("ultimo", sa.Integer(), nullable=False, server_default="0"),
        )

    # 4. Coluna alerta_vencimento_enviado_em em medidas_protetivas
    if not _coluna_existe("medidas_protetivas", "alerta_vencimento_enviado_em"):
        with op.batch_alter_table("medidas_protetivas") as batch_op:
            batch_op.add_column(sa.Column("alerta_vencimento_enviado_em", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    if _coluna_existe("medidas_protetivas", "alerta_vencimento_enviado_em"):
        with op.batch_alter_table("medidas_protetivas") as batch_op:
            batch_op.drop_column("alerta_vencimento_enviado_em")

    if _tabela_existe("sequencias_oficio"):
        op.drop_table("sequencias_oficio")

    if _tabela_existe("comunicacoes_interagencias"):
        op.drop_table("comunicacoes_interagencias")

    if _tabela_existe("notificacoes"):
        op.drop_table("notificacoes")
