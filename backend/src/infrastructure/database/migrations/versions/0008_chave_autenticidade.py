"""chave pública de autenticidade do documento emitido (RF08 / UC08)

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-21

- ``ocorrencias.chave_autenticidade``: chave alfanumérica de 24 caracteres, única,
  atribuída quando o Delegado valida a ocorrência (emissão do documento oficial).
- Ocorrências já validadas antes desta migração (``hash_narrativa`` preenchido)
  recebem uma chave retroativa para que seus comprovantes também sejam verificáveis.
- Idempotente: a coluna só é criada se ainda não existir.
"""
from __future__ import annotations

import secrets

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

TABELA = "ocorrencias"
COLUNA = "chave_autenticidade"
INDICE = "ix_ocorrencias_chave_autenticidade"

# Espelho de ``domain.ocorrencia.autenticidade`` — migrações não importam o domínio.
_ALFABETO_CHAVE = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_TAMANHO_CHAVE = 24


def _coluna_existe() -> bool:
    return COLUNA in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABELA)}


def _gerar_chave() -> str:
    return "".join(secrets.choice(_ALFABETO_CHAVE) for _ in range(_TAMANHO_CHAVE))


def _emitir_chaves_retroativas() -> None:
    conexao = op.get_bind()
    ids = conexao.execute(
        sa.text(f"SELECT id FROM {TABELA} WHERE hash_narrativa IS NOT NULL AND {COLUNA} IS NULL")
    ).scalars().all()
    for ocorrencia_id in ids:
        conexao.execute(
            sa.text(f"UPDATE {TABELA} SET {COLUNA} = :chave WHERE id = :id"),
            {"chave": _gerar_chave(), "id": ocorrencia_id},
        )


def upgrade() -> None:
    if not _coluna_existe():
        op.add_column(TABELA, sa.Column(COLUNA, sa.String(_TAMANHO_CHAVE), nullable=True))
        op.create_index(INDICE, TABELA, [COLUNA], unique=True)
    _emitir_chaves_retroativas()


def downgrade() -> None:
    if _coluna_existe():
        op.drop_index(INDICE, table_name=TABELA)
        op.drop_column(TABELA, COLUNA)
