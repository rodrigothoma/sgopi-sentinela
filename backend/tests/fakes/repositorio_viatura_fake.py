"""Repositório de viaturas in-memory."""
import copy
from uuid import UUID

from application.ports.outbound.repositorio_viatura import RepositorioViatura
from domain.shared.exceptions import ConflitoError
from domain.viatura.entity import SituacaoViatura, Viatura


class RepositorioViaturaFake(RepositorioViatura):
    def __init__(self) -> None:
        self._store: dict[UUID, Viatura] = {}

    async def salvar(self, viatura: Viatura) -> None:
        existente = self._store.get(viatura.id)
        if existente is not None and viatura.versao < existente.versao:
            raise ConflitoError("Versão desatualizada.", chave="generic.versao_desatualizada")
        self._store[viatura.id] = copy.deepcopy(viatura)

    async def buscar_por_id(self, viatura_id: UUID) -> Viatura | None:
        v = self._store.get(viatura_id)
        return copy.deepcopy(v) if v else None

    async def buscar_por_prefixo(self, prefixo: str) -> Viatura | None:
        return next((copy.deepcopy(v) for v in self._store.values() if v.prefixo == prefixo.upper()), None)

    async def buscar_por_placa(self, placa: str) -> Viatura | None:
        return next((copy.deepcopy(v) for v in self._store.values() if v.placa == placa.upper()), None)

    async def listar(self, situacoes: tuple[SituacaoViatura, ...] = ()) -> list[Viatura]:
        itens = [v for v in self._store.values() if not situacoes or v.situacao in situacoes]
        return [copy.deepcopy(v) for v in sorted(itens, key=lambda v: v.prefixo)]
