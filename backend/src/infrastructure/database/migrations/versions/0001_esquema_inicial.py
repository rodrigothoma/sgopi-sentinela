"""esquema inicial: usuarios, ocorrencias, envolvidos, tipificacoes, historico, auditoria, sequencias

Revision ID: 0001
Revises:
Create Date: 2026-09-13
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# RNF03*: tabelas append-only protegidas por trigger (apenas PostgreSQL)
_TABELAS_APPEND_ONLY = ("registros_auditoria", "historico_status_ocorrencia")


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("login", sa.String(100), nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column("papel", sa.String(30), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_usuarios_login", "usuarios", ["login"], unique=True)

    op.create_table(
        "ocorrencias",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("agente_policial_id", sa.Uuid(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("natureza", sa.String(255), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("localizacao", sa.String(500), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("data_hora_fato", sa.DateTime(timezone=True), nullable=False),
        sa.Column("numero_protocolo", sa.String(50), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="AGUARDANDO_REVISAO"),
        sa.Column("versao", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("validada_por_id", sa.Uuid(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("justificativa_revisao", sa.Text(), nullable=True),
        sa.Column("desfecho", sa.Text(), nullable=True),
        sa.Column("hash_narrativa", sa.String(64), nullable=True),
    )
    op.create_index("ix_ocorrencias_agente_policial_id", "ocorrencias", ["agente_policial_id"])
    op.create_index("ix_ocorrencias_status", "ocorrencias", ["status"])
    op.create_index("ix_ocorrencias_criada_em", "ocorrencias", ["criada_em"])

    op.create_table(
        "envolvidos",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ocorrencia_id", sa.Uuid(), sa.ForeignKey("ocorrencias.id"), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("documento", sa.String(50), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_envolvidos_ocorrencia_id", "envolvidos", ["ocorrencia_id"])

    op.create_table(
        "tipificacoes_ocorrencia",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ocorrencia_id", sa.Uuid(), sa.ForeignKey("ocorrencias.id"), nullable=False),
        sa.Column("artigo", sa.String(100), nullable=False),
        sa.Column("descricao", sa.String(500), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_tipificacoes_ocorrencia_ocorrencia_id", "tipificacoes_ocorrencia", ["ocorrencia_id"])

    op.create_table(
        "historico_status_ocorrencia",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ocorrencia_id", sa.Uuid(), sa.ForeignKey("ocorrencias.id"), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("de", sa.String(30), nullable=True),
        sa.Column("para", sa.String(30), nullable=False),
        sa.Column("em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("por_id", sa.Uuid(), nullable=False),
        sa.Column("justificativa", sa.Text(), nullable=True),
        sa.UniqueConstraint("ocorrencia_id", "ordem", name="uq_historico_ocorrencia_ordem"),
    )
    op.create_index("ix_historico_status_ocorrencia_ocorrencia_id", "historico_status_ocorrencia", ["ocorrencia_id"])

    op.create_table(
        "registros_auditoria",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("quem", sa.Uuid(), nullable=True),
        sa.Column("quando", sa.DateTime(timezone=True), nullable=False),
        sa.Column("operacao", sa.String(100), nullable=False),
        sa.Column("entidade", sa.String(100), nullable=False),
        sa.Column("entidade_id", sa.String(100), nullable=True),
        sa.Column("dados_antes", sa.JSON(), nullable=True),
        sa.Column("dados_depois", sa.JSON(), nullable=True),
        sa.Column("ip", sa.String(64), nullable=True),
    )
    op.create_index("ix_registros_auditoria_quem", "registros_auditoria", ["quem"])
    op.create_index("ix_registros_auditoria_quando", "registros_auditoria", ["quando"])
    op.create_index("ix_registros_auditoria_operacao", "registros_auditoria", ["operacao"])
    op.create_index("ix_registros_auditoria_entidade_id", "registros_auditoria", ["entidade_id"])

    op.create_table(
        "sequencias_protocolo",
        sa.Column("ano", sa.Integer(), primary_key=True),
        sa.Column("ultimo", sa.Integer(), nullable=False, server_default="0"),
    )

    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION sgopi_bloquear_alteracao() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'Tabela % é append-only (RNF03): % não permitido', TG_TABLE_NAME, TG_OP;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        for tabela in _TABELAS_APPEND_ONLY:
            op.execute(
                f"CREATE TRIGGER trg_{tabela}_append_only BEFORE UPDATE OR DELETE ON {tabela} "
                f"FOR EACH ROW EXECUTE FUNCTION sgopi_bloquear_alteracao();"
            )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for tabela in _TABELAS_APPEND_ONLY:
            op.execute(f"DROP TRIGGER IF EXISTS trg_{tabela}_append_only ON {tabela};")
        op.execute("DROP FUNCTION IF EXISTS sgopi_bloquear_alteracao();")
    for tabela in (
        "sequencias_protocolo",
        "registros_auditoria",
        "historico_status_ocorrencia",
        "tipificacoes_ocorrencia",
        "envolvidos",
        "ocorrencias",
        "usuarios",
    ):
        op.drop_table(tabela)
