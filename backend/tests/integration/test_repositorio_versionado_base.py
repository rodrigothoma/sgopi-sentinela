"""Classe base RepositorioVersionadoSQLAlchemy: salvar, buscar_por_id e concorrência otimista (RNF03).

Usa uma subclasse mínima sobre ViaturaModel (sem chaves estrangeiras) para exercitar só o
comportamento herdado, sem os métodos de busca específicos do repositório de viaturas.
"""
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Select, select

from adapters.outbound.persistence._concorrencia import RepositorioVersionadoSQLAlchemy
from adapters.outbound.persistence.mappers import ViaturaMapper
from domain.shared.exceptions import ConflitoError
from domain.viatura.entity import SituacaoViatura, Viatura
from infrastructure.database.models import ViaturaModel

AGORA = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)
MENSAGEM_CONFLITO = "Registro alterado por outro usuário."


class RepositorioMinimo(RepositorioVersionadoSQLAlchemy[ViaturaModel, Viatura]):
    _model_cls = ViaturaModel
    _mapper_cls = ViaturaMapper
    _mensagem_conflito = MENSAGEM_CONFLITO


class RepositorioComQueryPropria(RepositorioMinimo):
    """Registra os ids pedidos para provar que o gancho de query é usado por salvar e buscar_por_id."""

    def __init__(self, session) -> None:
        super().__init__(session)
        self.ids_consultados: list[UUID] = []

    def _query_carregar_model(self, entidade_id: UUID) -> Select[tuple[ViaturaModel]]:
        self.ids_consultados.append(entidade_id)
        return select(ViaturaModel).where(ViaturaModel.id == entidade_id)


async def test_salvar_insere_e_buscar_por_id_reconstitui_a_entidade(session_factory):
    viatura = Viatura(prefixo="VTR-01", placa="ABC1D23")
    async with session_factory() as s:
        await RepositorioMinimo(s).salvar(viatura)
        await s.commit()

    async with session_factory() as s:
        lida = await RepositorioMinimo(s).buscar_por_id(viatura.id)

    assert lida is not None and lida is not viatura
    assert (lida.prefixo, lida.placa, lida.versao) == ("VTR-01", "ABC1D23", 1)


async def test_buscar_por_id_inexistente_devolve_none(session):
    assert await RepositorioMinimo(session).buscar_por_id(uuid4()) is None


async def test_salvar_existente_atualiza_o_model(session_factory):
    viatura = Viatura(prefixo="VTR-01", placa="ABC1D23")
    async with session_factory() as s:
        await RepositorioMinimo(s).salvar(viatura)
        await s.commit()

    async with session_factory() as s:
        repo = RepositorioMinimo(s)
        lida = await repo.buscar_por_id(viatura.id)
        lida.marcar_indisponivel(AGORA)
        await repo.salvar(lida)
        await s.commit()

    async with session_factory() as s:
        relida = await RepositorioMinimo(s).buscar_por_id(viatura.id)
    assert (relida.situacao, relida.versao) == (SituacaoViatura.INDISPONIVEL, 2)


async def test_escrita_concorrente_obsoleta_usa_a_mensagem_da_subclasse(session_factory):
    viatura = Viatura(prefixo="VTR-01", placa="ABC1D23")
    async with session_factory() as s:
        await RepositorioMinimo(s).salvar(viatura)
        await s.commit()

    async with session_factory() as s1, session_factory() as s2:
        a = await RepositorioMinimo(s1).buscar_por_id(viatura.id)
        repo_b = RepositorioMinimo(s2)
        b = await repo_b.buscar_por_id(viatura.id)
        a.marcar_indisponivel(AGORA)
        await RepositorioMinimo(s1).salvar(a)
        await s1.commit()
        b.despachar(AGORA)
        with pytest.raises(ConflitoError) as erro:
            await repo_b.salvar(b)

    assert str(erro.value) == MENSAGEM_CONFLITO
    assert erro.value.chave == "generic.versao_desatualizada"


async def test_salvar_e_buscar_por_id_usam_a_query_da_subclasse(session):
    repo = RepositorioComQueryPropria(session)
    viatura = Viatura(prefixo="VTR-01", placa="ABC1D23")

    await repo.salvar(viatura)
    await repo.buscar_por_id(viatura.id)

    assert repo.ids_consultados == [viatura.id, viatura.id]
