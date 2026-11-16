"""Responsável opcional e exclusão lógica da frota.

Revision ID: 0018
Revises: 0017
"""
import sqlalchemy as sa
from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Preserva todos os cadastros existentes como ativos e sem responsável."""
    with op.batch_alter_table("viaturas") as batch:
        batch.add_column(sa.Column("responsavel", sa.String(120), nullable=True))
        batch.add_column(sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    """Reverte o esquema; executar somente após preservar os dados novos."""
    with op.batch_alter_table("viaturas") as batch:
        batch.drop_column("ativo")
        batch.drop_column("responsavel")
