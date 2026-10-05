"""
Porta de saída: RepositorioOcorrencia

Contrato (ABC) que isola os casos de uso de qualquer detalhe de persistência.
A implementação concreta (SQLAlchemy) fica em adapters/outbound/persistence/.
O repositório NÃO confirma transação — isso é papel da UnidadeDeTrabalho.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from domain.ocorrencia.entity import Ocorrencia, OrigemOcorrencia
from domain.ocorrencia.status import StatusOcorrencia


@dataclass(frozen=True)
class FiltroOcorrencias:
    status: tuple[StatusOcorrencia, ...] = field(default_factory=tuple)
    agente_policial_id: UUID | None = None
    limit: int = 50
    offset: int = 0
    # Padrão: mais antiga primeiro (fila do UC04); True para "minhas", que mostra as recentes
    mais_recentes_primeiro: bool = False
    # Sugestão #7: gravidade decrescente antes do critério de data (fila do Delegado e despacho)
    ordenar_por_prioridade: bool = False
    # Busca (sem diferenciar maiúsculas): trechos de natureza, protocolo e descrição/localização
    natureza: str | None = None
    protocolo: str | None = None
    texto: str | None = None
    origem: OrigemOcorrencia | None = None
    # Intervalo fechado sobre data_hora_fato
    data_fato_de: datetime | None = None
    data_fato_ate: datetime | None = None


class RepositorioOcorrencia(ABC):
    """Interface de persistência para o agregado Ocorrencia."""

    @abstractmethod
    async def salvar(self, ocorrencia: Ocorrencia) -> None:
        """Adiciona ou atualiza (com verificação de versão) a ocorrência na sessão corrente."""
        ...

    @abstractmethod
    async def buscar_por_id(self, ocorrencia_id: UUID) -> Ocorrencia | None: ...

    @abstractmethod
    async def buscar_por_protocolo(self, numero_protocolo: str) -> Ocorrencia | None:
        """Localiza a ocorrência pelo número de protocolo público (consulta do cidadão)."""
        ...

    @abstractmethod
    async def buscar_por_chave_autenticidade(self, chave: str) -> Ocorrencia | None:
        """Localiza o documento emitido pela chave pública (RF08); ``chave`` já na forma canônica."""
        ...

    @abstractmethod
    async def buscar_por_hash_narrativa(self, hash_narrativa: str) -> Ocorrencia | None:
        """Localiza o documento emitido pelo hash SHA-256 de verificação impresso (RF08)."""
        ...

    @abstractmethod
    async def listar(self, filtro: FiltroOcorrencias) -> list[Ocorrencia]:
        """Lista ordenada por criada_em (ascendente por padrão — UC04; ver ``mais_recentes_primeiro``),
        precedida pela prioridade decrescente quando ``ordenar_por_prioridade``."""
        ...

    @abstractmethod
    async def contar(self, filtro: FiltroOcorrencias) -> int: ...

    @abstractmethod
    async def lacre_em_uso(self, numero_lacre: str) -> bool:
        """RF03 / UC03 exceção I: o número de lacre é único em toda a base (qualquer ocorrência)."""
        ...
