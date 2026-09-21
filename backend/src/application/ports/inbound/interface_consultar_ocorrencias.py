"""Porta de entrada: consulta de ocorrências (RF13) — listagem paginada e detalhe completo."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_anexar_evidencia import EvidenciaOutput


@dataclass(frozen=True)
class ListarOcorrenciasInput:
    status: tuple[str, ...] = field(default_factory=tuple)
    limit: int = 50
    offset: int = 0
    somente_minhas: bool = False


@dataclass(frozen=True)
class EnvolvidoOutput:
    id: UUID
    nome: str
    tipo: str
    documento: str | None
    email: str | None = None
    telefone: str | None = None


@dataclass(frozen=True)
class TipificacaoOutput:
    artigo: str
    descricao: str


@dataclass(frozen=True)
class HistoricoStatusOutput:
    de: str | None
    para: str
    em: str
    por_id: UUID
    justificativa: str | None


@dataclass(frozen=True)
class OcorrenciaResumoOutput:
    ocorrencia_id: UUID
    numero_protocolo: str
    natureza: str
    localizacao: str
    latitude: float
    longitude: float
    status: str
    data_hora_fato: str
    criada_em: str
    atualizada_em: str
    agente_policial_id: UUID
    versao: int


@dataclass(frozen=True)
class OcorrenciaDetalheOutput(OcorrenciaResumoOutput):
    descricao: str = ""
    validada_por_id: UUID | None = None
    justificativa_revisao: str | None = None
    desfecho: str | None = None
    hash_narrativa: str | None = None
    narrativa_integra: bool | None = None
    chave_autenticidade: str | None = None
    envolvidos: tuple[EnvolvidoOutput, ...] = field(default_factory=tuple)
    tipificacoes: tuple[TipificacaoOutput, ...] = field(default_factory=tuple)
    evidencias: tuple[EvidenciaOutput, ...] = field(default_factory=tuple)
    historico_status: tuple[HistoricoStatusOutput, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PaginaOcorrenciasOutput:
    itens: tuple[OcorrenciaResumoOutput, ...]
    total: int
    limit: int
    offset: int


class InterfaceListarOcorrencias(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: ListarOcorrenciasInput) -> PaginaOcorrenciasOutput: ...


class InterfaceObterDetalheOcorrencia(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, ocorrencia_id: UUID) -> OcorrenciaDetalheOutput: ...
