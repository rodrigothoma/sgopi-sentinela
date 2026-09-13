"""
Models SQLAlchemy — mapeamento das entidades de domínio para tabelas relacionais.
Apenas adapters/ e infrastructure/ podem importar este módulo.
"""
from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.connection import Base


class OcorrenciaModel(Base):
    """Tabela principal de ocorrências policiais."""

    __tablename__ = "ocorrencias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agente_policial_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    natureza: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    localizacao: Mapped[str] = mapped_column(String(500), nullable=False)
    numero_protocolo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="REGISTRADA")
    criada_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    validada_por_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    envolvidos: Mapped[list[EnvolvidoModel]] = relationship(
        "EnvolvidoModel", back_populates="ocorrencia", cascade="all, delete-orphan"
    )
    tipificacoes: Mapped[list[TipificacaoModel]] = relationship(
        "TipificacaoModel", back_populates="ocorrencia", cascade="all, delete-orphan"
    )


class EnvolvidoModel(Base):
    """Tabela de envolvidos (vítimas, testemunhas, suspeitos) por ocorrência."""

    __tablename__ = "envolvidos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ocorrencia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ocorrencias.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    documento: Mapped[str | None] = mapped_column(String(50), nullable=True)

    ocorrencia: Mapped[OcorrenciaModel] = relationship("OcorrenciaModel", back_populates="envolvidos")


class TipificacaoModel(Base):
    """Tabela de tipificações penais vinculadas a uma ocorrência."""

    __tablename__ = "tipificacoes_ocorrencia"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ocorrencia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ocorrencias.id", ondelete="CASCADE"), nullable=False
    )
    artigo: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)

    ocorrencia: Mapped[OcorrenciaModel] = relationship("OcorrenciaModel", back_populates="tipificacoes")
