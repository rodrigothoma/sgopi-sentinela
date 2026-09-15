"""
Repositório in-memory para testes unitários.
Implementa RepositorioOcorrencia sem nenhum banco de dados real.
"""
import copy
from uuid import UUID

from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias, RepositorioOcorrencia
from domain.ocorrencia.entity import Ocorrencia
from domain.shared.exceptions import ConflitoError


class RepositorioOcorrenciaFake(RepositorioOcorrencia):
    """Fake em memória — zero I/O; simula verificação otimista de versão."""

    def __init__(self) -> None:
        self._store: dict[UUID, Ocorrencia] = {}

    async def salvar(self, ocorrencia: Ocorrencia) -> None:
        existente = self._store.get(ocorrencia.id)
        if existente is not None and ocorrencia.versao <= existente.versao and ocorrencia is not existente:
            raise ConflitoError("Versão desatualizada.", chave="generic.versao_desatualizada")
        self._store[ocorrencia.id] = copy.deepcopy(ocorrencia)

    async def buscar_por_id(self, ocorrencia_id: UUID) -> Ocorrencia | None:
        o = self._store.get(ocorrencia_id)
        return copy.deepcopy(o) if o else None

    async def buscar_por_chave_autenticidade(self, chave: str) -> Ocorrencia | None:
        for o in self._store.values():
            if o.chave_autenticidade == chave:
                return copy.deepcopy(o)
        return None

    def _filtrar(self, filtro: FiltroOcorrencias) -> list[Ocorrencia]:
        itens = list(self._store.values())
        if filtro.status:
            itens = [o for o in itens if o.status in filtro.status]
        if filtro.agente_policial_id:
            itens = [o for o in itens if o.agente_policial_id == filtro.agente_policial_id]
        return sorted(itens, key=lambda o: o.criada_em)

    async def listar(self, filtro: FiltroOcorrencias) -> list[Ocorrencia]:
        itens = self._filtrar(filtro)[filtro.offset : filtro.offset + filtro.limit]
        return [copy.deepcopy(o) for o in itens]

    async def contar(self, filtro: FiltroOcorrencias) -> int:
        return len(self._filtrar(filtro))
