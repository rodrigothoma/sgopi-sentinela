"""
Porta de saída: RepositorioOcorrencia

Contrato (ABC) que isola os casos de uso de qualquer detalhe de persistência.
A implementação concreta (SQLAlchemy) fica em adapters/outbound/persistence/.
O repositório NÃO confirma transação — isso é papel da UnidadeDeTrabalho.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

from domain.ocorrencia.entity import Ocorrencia
from domain.ocorrencia.status import StatusOcorrencia


@dataclass(frozen=True)
class FiltroOcorrencias:
    status: tuple[StatusOcorrencia, ...] = field(default_factory=tuple)
    agente_policial_id: UUID | None = None
    limit: int = 50
    offset: int = 0


class RepositorioOcorrencia(ABC):
    """Interface de persistência para o agregado Ocorrencia."""

    @abstractmethod
    async def salvar(self, ocorrencia: Ocorrencia) -> None:
        """Adiciona ou atualiza (com verificação de versão) a ocorrência na sessão corrente."""
        ...

    @abstractmethod
    async def buscar_por_id(self, ocorrencia_id: UUID) -> Ocorrencia | None: ...

    @abstractmethod
    async def listar(self, filtro: FiltroOcorrencias) -> list[Ocorrencia]:
        """Lista ordenada por criada_em ascendente (mais antiga primeiro — UC04)."""
        ...

    @abstractmethod
    async def contar(self, filtro: FiltroOcorrencias) -> int: ...
