"""Repositório de viaturas in-memory."""
import copy
from uuid import UUID

from application.ports.outbound.repositorio_viatura import RepositorioViatura
from domain.viatura.entity import SituacaoViatura, Viatura
from tests.fakes.controle_versao import ControleVersaoFake


class RepositorioViaturaFake(RepositorioViatura):
    def __init__(self) -> None:
        self._store: dict[UUID, Viatura] = {}
        self._versoes = ControleVersaoFake()

    def _copia(self, entidade: Viatura) -> Viatura:
        """Cópia isolada do armazenamento, registrada como carregada (como o repositório SQL)."""
        return self._versoes.ao_carregar(copy.deepcopy(entidade))

    async def salvar(self, viatura: Viatura) -> None:
        self._versoes.verificar(viatura, self._store.get(viatura.id))
        self._store[viatura.id] = copy.deepcopy(viatura)
        self._versoes.ao_salvar(viatura)

    async def buscar_por_id(self, viatura_id: UUID) -> Viatura | None:
        v = self._store.get(viatura_id)
        return self._copia(v) if v else None

    async def buscar_por_prefixo(self, prefixo: str) -> Viatura | None:
        return next((self._copia(v) for v in self._store.values() if v.prefixo == prefixo.upper()), None)

    async def buscar_por_placa(self, placa: str) -> Viatura | None:
        return next((self._copia(v) for v in self._store.values() if v.placa == placa.upper()), None)

    async def listar(self, situacoes: tuple[SituacaoViatura, ...] = ()) -> list[Viatura]:
        itens = [v for v in self._store.values() if not situacoes or v.situacao in situacoes]
        return [self._copia(v) for v in sorted(itens, key=lambda v: v.prefixo)]
