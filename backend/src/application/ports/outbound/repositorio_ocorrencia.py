"""
Porta de saída: RepositorioOcorrencia

Contrato (ABC) que isola os casos de uso de qualquer detalhe de persistência.
A implementação concreta (SQLAlchemy) fica em adapters/outbound/persistence/.
"""
from abc import ABC, abstractmethod
from uuid import UUID

from domain.ocorrencia.entity import Ocorrencia


class RepositorioOcorrencia(ABC):
    """Interface de persistência para a entidade Ocorrencia."""

    @abstractmethod
    async def salvar(self, ocorrencia: Ocorrencia) -> None:
        """Persiste uma ocorrência nova ou atualiza uma existente."""
        ...

    @abstractmethod
    async def buscar_por_id(self, ocorrencia_id: UUID) -> Ocorrencia | None:
        """Retorna a ocorrência pelo ID ou None se não existir."""
        ...

    @abstractmethod
    async def listar(self, status: str | None = None) -> list[Ocorrencia]:
        """Retorna ocorrências, com filtro opcional por status."""
        ...
