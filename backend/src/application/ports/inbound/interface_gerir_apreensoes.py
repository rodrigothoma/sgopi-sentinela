"""Porta de entrada: itens apreendidos, cadeia de custódia e Auto de Apreensão (RF03 / UC03)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

from application.ports.inbound.ator import Ator


@dataclass(frozen=True)
class RegistrarItemApreendidoInput:
    ocorrencia_id: UUID
    tipo: str
    descricao: str
    quantidade: int
    estado_conservacao: str
    numero_lacre: str
    localizacao_deposito: str
    unidade: str = "UNIDADE"
    numero_serie: str | None = None
    marca: str | None = None
    calibre: str | None = None


@dataclass(frozen=True)
class MovimentarCustodiaInput:
    ocorrencia_id: UUID
    item_id: UUID
    destino: str
    observacao: str | None = None


@dataclass(frozen=True)
class MovimentacaoCustodiaOutput:
    em: str
    por_id: UUID
    origem: str | None
    destino: str
    observacao: str | None


@dataclass(frozen=True)
class ItemApreendidoOutput:
    id: UUID
    tipo: str
    descricao: str
    quantidade: int
    unidade: str
    estado_conservacao: str
    numero_lacre: str
    numero_serie: str | None
    marca: str | None
    calibre: str | None
    localizacao_deposito: str
    localizacao_atual: str
    registrado_em: str
    registrado_por_id: UUID
    movimentacoes: tuple[MovimentacaoCustodiaOutput, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AutoApreensaoOutput:
    """Documento imprimível: identificador único, dados da ocorrência, itens e hash de integridade."""

    numero: str
    ocorrencia_id: UUID
    numero_protocolo: str
    natureza: str
    localizacao: str
    data_hora_fato: str
    status: str
    agente_policial_id: UUID
    emitido_em: str
    emitido_por_id: UUID
    hash_sha256: str
    itens: tuple[ItemApreendidoOutput, ...] = field(default_factory=tuple)


class InterfaceRegistrarItemApreendido(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: RegistrarItemApreendidoInput) -> ItemApreendidoOutput: ...


class InterfaceMovimentarCustodia(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: MovimentarCustodiaInput) -> ItemApreendidoOutput: ...


class InterfaceEmitirAutoApreensao(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, ocorrencia_id: UUID) -> AutoApreensaoOutput: ...
