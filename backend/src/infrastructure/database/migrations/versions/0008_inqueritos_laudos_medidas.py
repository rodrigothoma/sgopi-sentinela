"""inqueritos, laudos_periciais, medidas_protetivas e sequencias associadas

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-27
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Inquéritos Policiais (RF06 / UC06)
    op.create_table(
        "inqueritos",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("numero", sa.String(50), nullable=False, unique=True),
        sa.Column("ementa", sa.Text(), nullable=False),
        sa.Column("delegado_id", sa.Uuid(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="EM_ANDAMENTO"),
        sa.Column("relatorio_final", sa.Text(), nullable=True),
        sa.Column("motivo_arquivamento", sa.Text(), nullable=True),
        sa.Column("data_abertura", sa.DateTime(timezone=True), nullable=False),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("versao", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_inqueritos_numero", "inqueritos", ["numero"], unique=True)
    op.create_index("ix_inqueritos_delegado_id", "inqueritos", ["delegado_id"])
    op.create_index("ix_inqueritos_status", "inqueritos", ["status"])
    op.create_index("ix_inqueritos_data_abertura", "inqueritos", ["data_abertura"])

    # 2. Vínculo de Ocorrências a Inquérito
    op.add_column("ocorrencias", sa.Column("inquerito_id", sa.Uuid(), sa.ForeignKey("inqueritos.id"), nullable=True))
    op.create_index("ix_ocorrencias_inquerito_id", "ocorrencias", ["inquerito_id"])

    # 3. Laudos Periciais (RF07 / UC07)
    op.create_table(
        "laudos_periciais",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("numero_referencia", sa.String(50), nullable=False, unique=True),
        sa.Column("tipo_pericia", sa.String(50), nullable=False),
        sa.Column("descricao_solicitacao", sa.Text(), nullable=False),
        sa.Column("solicitante_id", sa.Uuid(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("perito_id", sa.Uuid(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("ocorrencia_id", sa.Uuid(), sa.ForeignKey("ocorrencias.id"), nullable=True),
        sa.Column("inquerito_id", sa.Uuid(), sa.ForeignKey("inqueritos.id"), nullable=True),
        sa.Column("item_apreendido_id", sa.Uuid(), sa.ForeignKey("itens_apreendidos.id"), nullable=True),
        sa.Column("conclusoes_tecnicas", sa.Text(), nullable=True),
        sa.Column("arquivo_chave", sa.String(255), nullable=True),
        sa.Column("arquivo_nome", sa.String(255), nullable=True),
        sa.Column("hash_sha256", sa.String(64), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="SOLICITADO"),
        sa.Column("solicitado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("versao", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_laudos_periciais_numero_referencia", "laudos_periciais", ["numero_referencia"], unique=True)
    op.create_index("ix_laudos_periciais_tipo_pericia", "laudos_periciais", ["tipo_pericia"])
    op.create_index("ix_laudos_periciais_ocorrencia_id", "laudos_periciais", ["ocorrencia_id"])
    op.create_index("ix_laudos_periciais_inquerito_id", "laudos_periciais", ["inquerito_id"])
    op.create_index("ix_laudos_periciais_item_apreendido_id", "laudos_periciais", ["item_apreendido_id"])
    op.create_index("ix_laudos_periciais_hash_sha256", "laudos_periciais", ["hash_sha256"])
    op.create_index("ix_laudos_periciais_status", "laudos_periciais", ["status"])
    op.create_index("ix_laudos_periciais_solicitado_em", "laudos_periciais", ["solicitado_em"])

    # 4. Medidas Protetivas (RF09 / UC09)
    op.create_table(
        "medidas_protetivas",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("numero_referencia", sa.String(50), nullable=False, unique=True),
        sa.Column("ocorrencia_id", sa.Uuid(), sa.ForeignKey("ocorrencias.id"), nullable=False),
        sa.Column("delegado_id", sa.Uuid(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("vitima_id", sa.Uuid(), nullable=False),
        sa.Column("agressor_id", sa.Uuid(), nullable=False),
        sa.Column("tipos_restricao", sa.JSON(), nullable=False),
        sa.Column("distancia_minima_metros", sa.Integer(), nullable=True),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("prazo_dias", sa.Integer(), nullable=False),
        sa.Column("data_vencimento", sa.Date(), nullable=False),
        sa.Column("condicoes_especificas", sa.Text(), nullable=True),
        sa.Column("motivo_revogacao", sa.Text(), nullable=True),
        sa.Column("justificativa_renovacao", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ATIVA"),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("versao", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_medidas_protetivas_numero_referencia", "medidas_protetivas", ["numero_referencia"], unique=True)
    op.create_index("ix_medidas_protetivas_ocorrencia_id", "medidas_protetivas", ["ocorrencia_id"])
    op.create_index("ix_medidas_protetivas_vitima_id", "medidas_protetivas", ["vitima_id"])
    op.create_index("ix_medidas_protetivas_agressor_id", "medidas_protetivas", ["agressor_id"])
    op.create_index("ix_medidas_protetivas_data_vencimento", "medidas_protetivas", ["data_vencimento"])
    op.create_index("ix_medidas_protetivas_status", "medidas_protetivas", ["status"])
    op.create_index("ix_medidas_protetivas_criada_em", "medidas_protetivas", ["criada_em"])

    # 5. Tabelas sequenciais
    op.create_table(
        "sequencias_inquerito",
        sa.Column("ano", sa.Integer(), primary_key=True),
        sa.Column("ultimo", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "sequencias_laudo",
        sa.Column("ano", sa.Integer(), primary_key=True),
        sa.Column("ultimo", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "sequencias_medida",
        sa.Column("ano", sa.Integer(), primary_key=True),
        sa.Column("ultimo", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("sequencias_medida")
    op.drop_table("sequencias_laudo")
    op.drop_table("sequencias_inquerito")
    op.drop_table("medidas_protetivas")
    op.drop_table("laudos_periciais")
    op.drop_index("ix_ocorrencias_inquerito_id", "ocorrencias")
    op.drop_column("ocorrencias", "inquerito_id")
    op.drop_table("inqueritos")
