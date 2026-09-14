"""Fakes de despacho: RepositorioOrdemDespachoFake e GeradorNumeroOrdemFake."""
import copy
from uuid import UUID

from application.ports.outbound.gerador_numero_ordem import GeradorNumeroOrdem, formatar_numero_ordem
from application.ports.outbound.repositorio_ordem_despacho import RepositorioOrdemDespacho
from domain.despacho.entity import OrdemDeDespacho


class RepositorioOrdemDespachoFake(RepositorioOrdemDespacho):
    def __init__(self) -> None:
        self._store: dict[UUID, OrdemDeDespacho] = {}

    async def salvar(self, ordem: OrdemDeDespacho) -> None:
        self._store[ordem.id] = copy.deepcopy(ordem)

    async def buscar_por_id(self, ordem_id: UUID) -> OrdemDeDespacho | None:
        o = self._store.get(ordem_id)
        return copy.deepcopy(o) if o else None

    async def listar(self, ocorrencia_id=None, somente_ativas=False, limit=100):
        itens = list(self._store.values())
        if ocorrencia_id:
            itens = [o for o in itens if o.ocorrencia_id == ocorrencia_id]
        if somente_ativas:
            itens = [o for o in itens if o.ativa]
        return [copy.deepcopy(o) for o in sorted(itens, key=lambda o: o.criada_em, reverse=True)[:limit]]


class GeradorNumeroOrdemFake(GeradorNumeroOrdem):
    def __init__(self, falhar: bool = False) -> None:
        self._n = 0
        self.falhar = falhar

    async def proximo(self, ano: int) -> str:
        if self.falhar:
            raise RuntimeError("falha simulada ao gerar número da ordem")
        self._n += 1
        return formatar_numero_ordem(ano, self._n)
