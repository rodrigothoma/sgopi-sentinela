"""chave pública de autenticidade do documento emitido (RF08)

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-14
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("ocorrencias") as batch:
        batch.add_column(sa.Column("chave_autenticidade", sa.String(24), nullable=True))
    op.create_index(
        "ix_ocorrencias_chave_autenticidade", "ocorrencias", ["chave_autenticidade"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_ocorrencias_chave_autenticidade", table_name="ocorrencias")
    with op.batch_alter_table("ocorrencias") as batch:
        batch.drop_column("chave_autenticidade")
