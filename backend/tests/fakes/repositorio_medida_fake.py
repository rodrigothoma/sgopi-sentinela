"""Fake em memória do repositório de Medidas Protetivas (RF09)."""
import copy
from uuid import UUID

from application.ports.outbound.repositorio_medida_protetiva import RepositorioMedidaProtetiva
from domain.medida_protetiva.entity import MedidaProtetiva, StatusMedida


class RepositorioMedidaProtetivaFake(RepositorioMedidaProtetiva):
    def __init__(self) -> None:
        self._store: dict[UUID, MedidaProtetiva] = {}

    async def salvar(self, medida: MedidaProtetiva) -> None:
        self._store[medida.id] = copy.deepcopy(medida)

    async def buscar_por_id(self, medida_id: UUID) -> MedidaProtetiva | None:
        medida = self._store.get(medida_id)
        return copy.deepcopy(medida) if medida else None

    async def buscar_por_referencia(self, numero_referencia: str) -> MedidaProtetiva | None:
        return next((copy.deepcopy(m) for m in self._store.values() if m.numero_referencia == numero_referencia), None)

    async def listar(
        self,
        status: list[StatusMedida] | None = None,
        ocorrencia_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MedidaProtetiva], int]:
        itens = [m for m in self._store.values() if (not status or m.status in status) and (not ocorrencia_id or m.ocorrencia_id == ocorrencia_id)]
        itens.sort(key=lambda m: m.criada_em, reverse=True)
        return [copy.deepcopy(m) for m in itens[offset : offset + limit]], len(itens)
