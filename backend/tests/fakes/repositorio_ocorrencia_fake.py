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

    async def buscar_por_protocolo(self, numero_protocolo: str) -> Ocorrencia | None:
        return next((copy.deepcopy(o) for o in self._store.values() if o.numero_protocolo == numero_protocolo), None)

    async def buscar_por_chave_autenticidade(self, chave: str) -> Ocorrencia | None:
        return next((copy.deepcopy(o) for o in self._store.values() if o.chave_autenticidade == chave), None)

    async def buscar_por_hash_narrativa(self, hash_narrativa: str) -> Ocorrencia | None:
        candidatos = sorted((o for o in self._store.values() if o.hash_narrativa == hash_narrativa), key=lambda o: o.criada_em)
        return copy.deepcopy(candidatos[0]) if candidatos else None

    def _filtrar(self, filtro: FiltroOcorrencias) -> list[Ocorrencia]:
        itens = list(self._store.values())
        if filtro.status:
            itens = [o for o in itens if o.status in filtro.status]
        if filtro.agente_policial_id:
            itens = [o for o in itens if o.agente_policial_id == filtro.agente_policial_id]
        itens = [o for o in itens if _atende_busca(o, filtro)]
        itens = sorted(itens, key=lambda o: o.criada_em, reverse=filtro.mais_recentes_primeiro)
        if filtro.ordenar_por_prioridade:
            itens = sorted(itens, key=lambda o: o.prioridade.peso, reverse=True)  # estável: mantém a data como desempate
        return itens

    async def listar(self, filtro: FiltroOcorrencias) -> list[Ocorrencia]:
        itens = self._filtrar(filtro)[filtro.offset : filtro.offset + filtro.limit]
        return [copy.deepcopy(o) for o in itens]

    async def contar(self, filtro: FiltroOcorrencias) -> int:
        return len(self._filtrar(filtro))

    async def lacre_em_uso(self, numero_lacre: str) -> bool:
        return any(i.numero_lacre == numero_lacre for o in self._store.values() for i in o.itens_apreendidos)


def _contem(campo: str, termo: str | None) -> bool:
    return termo is None or termo.casefold() in campo.casefold()


def _atende_busca(o: Ocorrencia, filtro: FiltroOcorrencias) -> bool:
    return (
        _contem(o.natureza, filtro.natureza)
        and _contem(o.numero_protocolo, filtro.protocolo)
        and (_contem(o.descricao, filtro.texto) or _contem(o.localizacao, filtro.texto))
        and (filtro.origem is None or o.origem == filtro.origem)
        and (filtro.data_fato_de is None or o.data_hora_fato >= filtro.data_fato_de)
        and (filtro.data_fato_ate is None or o.data_hora_fato <= filtro.data_fato_ate)
    )
