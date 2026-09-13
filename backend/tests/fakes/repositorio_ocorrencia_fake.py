"""
Repositório in-memory para testes unitários.
Implementa RepositorioOcorrencia sem nenhum banco de dados real.
"""
from uuid import UUID

from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from domain.ocorrencia.entity import Ocorrencia


class RepositorioOcorrenciaFake(RepositorioOcorrencia):
    """Fake em memória — zero I/O, ideal para testes unitários rápidos."""

    def __init__(self) -> None:
        self._store: dict[UUID, Ocorrencia] = {}

    async def salvar(self, ocorrencia: Ocorrencia) -> None:
        self._store[ocorrencia.id] = ocorrencia

    async def buscar_por_id(self, ocorrencia_id: UUID) -> Ocorrencia | None:
        return self._store.get(ocorrencia_id)

    async def listar(self, status: str | None = None) -> list[Ocorrencia]:
        ocorrencias = list(self._store.values())
        if status:
            ocorrencias = [o for o in ocorrencias if o.status.value == status]
        return ocorrencias
