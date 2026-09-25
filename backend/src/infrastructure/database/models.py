"""
Models SQLAlchemy — mapeamento das entidades de domínio para tabelas relacionais.
Apenas adapters/ e infrastructure/ podem importar este módulo.

RNF03*: nenhuma cascata de exclusão; filhos removidos do agregado são marcados
``ativo = False``; ``historico_status_ocorrencia`` e ``registros_auditoria``
são append-only (trigger no Postgres — ver migration 0001).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.connection import Base


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    papel: Mapped[str] = mapped_column(String(30), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class OcorrenciaModel(Base):
    """Tabela principal de ocorrências policiais."""

    __tablename__ = "ocorrencias"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    agente_policial_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuarios.id"), nullable=False, index=True)
    natureza: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    localizacao: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    data_hora_fato: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    numero_protocolo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="AGUARDANDO_REVISAO", index=True)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    atualizada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    validada_por_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("usuarios.id"), nullable=True)
    justificativa_revisao: Mapped[str | None] = mapped_column(Text, nullable=True)
    desfecho: Mapped[str | None] = mapped_column(Text, nullable=True)
    hash_narrativa: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # RF20: arquivamento / exclusão lógica autorizados pelo Delegado, sempre com motivo
    arquivada_por_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("usuarios.id"), nullable=True)
    motivo_arquivamento: Mapped[str | None] = mapped_column(Text, nullable=True)
    excluida_por_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("usuarios.id"), nullable=True)
    motivo_exclusao: Mapped[str | None] = mapped_column(Text, nullable=True)

    # optimistic locking (RNF11): ``versao`` é controlada pelo domínio e verificada
    # explicitamente pelo repositório (SELECT … FOR UPDATE + comparação).

    envolvidos: Mapped[list[EnvolvidoModel]] = relationship("EnvolvidoModel", back_populates="ocorrencia")
    tipificacoes: Mapped[list[TipificacaoModel]] = relationship("TipificacaoModel", back_populates="ocorrencia")
    historico: Mapped[list[HistoricoStatusModel]] = relationship(
        "HistoricoStatusModel", order_by="HistoricoStatusModel.ordem"
    )
    evidencias: Mapped[list[EvidenciaModel]] = relationship(
        "EvidenciaModel", order_by="EvidenciaModel.enviada_em", back_populates="ocorrencia"
    )
    itens_apreendidos: Mapped[list[ItemApreendidoModel]] = relationship(
        "ItemApreendidoModel", order_by="ItemApreendidoModel.registrado_em", back_populates="ocorrencia"
    )


class EnvolvidoModel(Base):
    """Tabela de envolvidos (vítimas, testemunhas, suspeitos) por ocorrência."""

    __tablename__ = "envolvidos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ocorrencia_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("ocorrencias.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    documento: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    ocorrencia: Mapped[OcorrenciaModel] = relationship("OcorrenciaModel", back_populates="envolvidos")


class TipificacaoModel(Base):
    """Tabela de tipificações penais vinculadas a uma ocorrência."""

    __tablename__ = "tipificacoes_ocorrencia"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ocorrencia_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("ocorrencias.id"), nullable=False, index=True)
    artigo: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    ocorrencia: Mapped[OcorrenciaModel] = relationship("OcorrenciaModel", back_populates="tipificacoes")


class HistoricoStatusModel(Base):
    """Histórico append-only de transições de status (RNF03*)."""

    __tablename__ = "historico_status_ocorrencia"
    __table_args__ = (UniqueConstraint("ocorrencia_id", "ordem", name="uq_historico_ocorrencia_ordem"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ocorrencia_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("ocorrencias.id"), nullable=False, index=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    de: Mapped[str | None] = mapped_column(String(30), nullable=True)
    para: Mapped[str] = mapped_column(String(30), nullable=False)
    em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    por_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    justificativa: Mapped[str | None] = mapped_column(Text, nullable=True)


class EvidenciaModel(Base):
    """Metadados append-only de uma evidência armazenada fora do banco."""

    __tablename__ = "evidencias"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ocorrencia_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("ocorrencias.id"), nullable=False, index=True)
    nome_original: Mapped[str] = mapped_column(String(255), nullable=False)
    formato: Mapped[str] = mapped_column(String(10), nullable=False)
    tamanho: Mapped[int] = mapped_column(Integer, nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    chave_armazenamento: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    enviada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    ocorrencia: Mapped[OcorrenciaModel] = relationship("OcorrenciaModel", back_populates="evidencias")


class ItemApreendidoModel(Base):
    """Item apreendido (RF03): vínculo permanente à ocorrência; lacre único em toda a base (UC03 exc. I)."""

    __tablename__ = "itens_apreendidos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ocorrencia_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("ocorrencias.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    unidade: Mapped[str] = mapped_column(String(20), nullable=False, default="UNIDADE")
    estado_conservacao: Mapped[str] = mapped_column(String(20), nullable=False)
    numero_lacre: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    numero_serie: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    marca: Mapped[str | None] = mapped_column(String(100), nullable=True)
    calibre: Mapped[str | None] = mapped_column(String(50), nullable=True)
    localizacao_deposito: Mapped[str] = mapped_column(String(255), nullable=False)
    registrado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    registrado_por_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuarios.id"), nullable=False)

    ocorrencia: Mapped[OcorrenciaModel] = relationship("OcorrenciaModel", back_populates="itens_apreendidos")
    movimentacoes: Mapped[list[MovimentacaoCustodiaModel]] = relationship(
        "MovimentacaoCustodiaModel", order_by="MovimentacaoCustodiaModel.ordem"
    )


class MovimentacaoCustodiaModel(Base):
    """Cadeia de custódia append-only (RF03 / RNF03*): quem, quando, de onde, para onde."""

    __tablename__ = "movimentacoes_custodia"
    __table_args__ = (UniqueConstraint("item_id", "ordem", name="uq_movimentacao_item_ordem"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("itens_apreendidos.id"), nullable=False, index=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    por_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    origem: Mapped[str | None] = mapped_column(String(255), nullable=True)
    destino: Mapped[str] = mapped_column(String(255), nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)


class RegistroAuditoriaModel(Base):
    """Auditoria append-only (RF20 / RNF03*)."""

    __tablename__ = "registros_auditoria"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    quem: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    quando: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    operacao: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entidade: Mapped[str] = mapped_column(String(100), nullable=False)
    entidade_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    dados_antes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dados_depois: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)


class SequenciaProtocoloModel(Base):
    """Contador por ano para SGOPI-AAAA-NNNNNN (HEX-08)."""

    __tablename__ = "sequencias_protocolo"

    ano: Mapped[int] = mapped_column(Integer, primary_key=True)
    ultimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ViaturaModel(Base):
    """Frota (RF15) com última posição desnormalizada (RF16)."""

    __tablename__ = "viaturas"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    prefixo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    placa: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), nullable=False, default="DISPONIVEL", index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    posicao_registrada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    atualizada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OrdemDespachoModel(Base):
    """Ordem de despacho (RF18): data/hora, operador, viatura e ocorrência (critério 5 do MVP)."""

    __tablename__ = "ordens_despacho"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    numero: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    ocorrencia_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("ocorrencias.id"), nullable=False, index=True)
    viatura_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("viaturas.id"), nullable=False, index=True)
    operador_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuarios.id"), nullable=False)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    encerrada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SequenciaOrdemDespachoModel(Base):
    """Contador por ano para OD-AAAA-NNNNNN."""

    __tablename__ = "sequencias_ordem_despacho"

    ano: Mapped[int] = mapped_column(Integer, primary_key=True)
    ultimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
