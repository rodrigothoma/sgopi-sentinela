"""Contrato de concorrência otimista (RNF03) para RepositorioOcorrencia e RepositorioViatura.

Garante que as fakes usadas nos testes unitários se comportam como os adaptadores SQL (LSP).
"""
from datetime import UTC, datetime, timedelta

import pytest

from adapters.outbound.persistence.ocorrencia_repositorio_sqlalchemy import OcorrenciaRepositorioSQLAlchemy
from adapters.outbound.persistence.viatura_repositorio_sqlalchemy import ViaturaRepositorioSQLAlchemy
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipoEnvolvido
from domain.shared.exceptions import ConflitoError
from domain.shared.geo import Coordenada
from domain.viatura.entity import SituacaoViatura, Viatura
from tests.fakes.repositorio_ocorrencia_fake import RepositorioOcorrenciaFake
from tests.fakes.repositorio_viatura_fake import RepositorioViaturaFake
from tests.integration.conftest import IDS
from tests.integration.contratos.conftest import IMPLEMENTACOES, sessoes_fake, sessoes_sqlalchemy

AGORA = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)


@pytest.fixture
def sessoes_ocorrencia(request, implementacao):
    if implementacao == "fake":
        return sessoes_fake(RepositorioOcorrenciaFake())
    request.getfixturevalue("usuarios")
    return sessoes_sqlalchemy(request.getfixturevalue("session_factory"), OcorrenciaRepositorioSQLAlchemy)


@pytest.fixture
def sessoes_viatura(request, implementacao):
    if implementacao == "fake":
        return sessoes_fake(RepositorioViaturaFake())
    return sessoes_sqlalchemy(request.getfixturevalue("session_factory"), ViaturaRepositorioSQLAlchemy)


def _ocorrencia(agente_id) -> Ocorrencia:
    return Ocorrencia.registrar(
        agente_policial_id=agente_id,
        natureza="Furto",
        descricao="Furto de veículo em via pública, sem violência.",
        localizacao="Av. Brasil, 500",
        coordenada=Coordenada(-29.78, -55.79),
        data_hora_fato=AGORA - timedelta(hours=1),
        numero_protocolo="SGOPI-2026-000001",
        agora=AGORA,
        envolvidos=[Envolvido(nome="Maria", tipo=TipoEnvolvido.VITIMA)],
    )


AGENTE = IDS["agente"]
DELEGADO = IDS["delegado"]


@IMPLEMENTACOES
async def test_ocorrencia_round_trip_devolve_copia_isolada(sessoes_ocorrencia):
    original = _ocorrencia(AGENTE)
    async with sessoes_ocorrencia() as s:
        await s.repo.salvar(original)
        await s.commit()
    async with sessoes_ocorrencia() as s:
        lida = await s.repo.buscar_por_id(original.id)

    assert lida is not original
    assert (lida.numero_protocolo, lida.versao, lida.status) == (original.numero_protocolo, 1, original.status)


@IMPLEMENTACOES
async def test_ocorrencia_salvar_sem_alteracao_e_aceito(sessoes_ocorrencia):
    original = _ocorrencia(AGENTE)
    async with sessoes_ocorrencia() as s:
        await s.repo.salvar(original)
        await s.commit()
    async with sessoes_ocorrencia() as s:
        lida = await s.repo.buscar_por_id(original.id)
        await s.repo.salvar(lida)


@IMPLEMENTACOES
async def test_ocorrencia_escrita_concorrente_obsoleta_e_recusada(sessoes_ocorrencia):
    original = _ocorrencia(AGENTE)
    async with sessoes_ocorrencia() as s:
        await s.repo.salvar(original)
        await s.commit()

    async with sessoes_ocorrencia() as s1, sessoes_ocorrencia() as s2:
        a = await s1.repo.buscar_por_id(original.id)
        b = await s2.repo.buscar_por_id(original.id)
        a.validar(DELEGADO, AGORA)
        await s1.repo.salvar(a)
        await s1.commit()
        b.rejeitar(DELEGADO, "Fato atípico e sem materialidade.", AGORA)
        with pytest.raises(ConflitoError):
            await s2.repo.salvar(b)


@IMPLEMENTACOES
async def test_viatura_salvar_sem_alteracao_e_aceito(sessoes_viatura):
    viatura = Viatura(prefixo="VTR-01", placa="ABC1D23")
    async with sessoes_viatura() as s:
        await s.repo.salvar(viatura)
        await s.commit()
    async with sessoes_viatura() as s:
        lida = await s.repo.buscar_por_id(viatura.id)
        await s.repo.salvar(lida)


@IMPLEMENTACOES
async def test_viatura_escrita_concorrente_obsoleta_e_recusada(sessoes_viatura):
    viatura = Viatura(prefixo="VTR-01", placa="ABC1D23")
    async with sessoes_viatura() as s:
        await s.repo.salvar(viatura)
        await s.commit()

    async with sessoes_viatura() as s1, sessoes_viatura() as s2:
        a = await s1.repo.buscar_por_id(viatura.id)
        b = await s2.repo.buscar_por_id(viatura.id)
        a.marcar_indisponivel(AGORA)
        await s1.repo.salvar(a)
        await s1.commit()
        b.despachar(AGORA)
        with pytest.raises(ConflitoError):
            await s2.repo.salvar(b)

    async with sessoes_viatura() as s:
        assert (await s.repo.buscar_por_id(viatura.id)).situacao == SituacaoViatura.INDISPONIVEL
