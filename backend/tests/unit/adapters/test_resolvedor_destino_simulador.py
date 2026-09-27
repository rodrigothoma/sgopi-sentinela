"""ResolvedorDestino do simulador (issue #54, RF02).

Destino lido dos repositórios existentes, sem alterar portas nem domínio.
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest

from adapters.inbound.simulador.resolvedor_destino import ResolvedorDestinoRepositorios, ResolvedorDestinoSessao
from domain.despacho.entity import OrdemDeDespacho
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipoEnvolvido
from domain.shared.geo import Coordenada
from tests.fakes.atores import OPERADOR
from tests.fakes.despacho_fake import RepositorioOrdemDespachoFake
from tests.fakes.repositorio_ocorrencia_fake import RepositorioOcorrenciaFake
from tests.unit.use_cases.conftest import AGORA

DESTINO = Coordenada(-29.7800, -55.7900)


async def _ocorrencia(repo: RepositorioOcorrenciaFake) -> Ocorrencia:
    o = Ocorrencia.registrar(
        agente_policial_id=uuid4(),
        natureza="Furto",
        descricao="descrição circunstanciada com mais de vinte caracteres",
        localizacao="Rua A, Centro",
        coordenada=DESTINO,
        data_hora_fato=AGORA,
        numero_protocolo="SGOPI-2026-000001",
        agora=AGORA,
        envolvidos=[Envolvido(nome="Vítima Teste", tipo=TipoEnvolvido.VITIMA)],
    )
    await repo.salvar(o)
    return o


async def test_ordem_ativa_resolve_para_coordenada_da_ocorrencia():
    ocorrencias, ordens = RepositorioOcorrenciaFake(), RepositorioOrdemDespachoFake()
    o = await _ocorrencia(ocorrencias)
    viatura_id = uuid4()
    await ordens.salvar(
        OrdemDeDespacho(
            numero="OD-2026-000001",
            ocorrencia_id=o.id,
            viatura_id=viatura_id,
            operador_id=OPERADOR.id,
            criada_em=AGORA,
        )
    )
    destinos = await ResolvedorDestinoRepositorios(ordens, ocorrencias).destinos([viatura_id, uuid4()])
    assert destinos == {viatura_id: DESTINO}


async def test_ordem_encerrada_nao_resolve_destino():
    ocorrencias, ordens = RepositorioOcorrenciaFake(), RepositorioOrdemDespachoFake()
    o = await _ocorrencia(ocorrencias)
    viatura_id = uuid4()
    ordem = OrdemDeDespacho(
        numero="OD-2026-000002",
        ocorrencia_id=o.id,
        viatura_id=viatura_id,
        operador_id=OPERADOR.id,
        criada_em=AGORA,
    )
    ordem.encerrar(AGORA)
    await ordens.salvar(ordem)
    destinos = await ResolvedorDestinoRepositorios(ordens, ocorrencias).destinos([viatura_id])
    assert destinos == {}


async def test_erro_de_leitura_vira_sem_destino_sem_derrubar_o_tick():
    class OrdensQuebradas(RepositorioOrdemDespachoFake):
        async def listar(self, *args, **kwargs):
            raise ConnectionError("banco fora do ar")

    destinos = await ResolvedorDestinoRepositorios(
        OrdensQuebradas(), RepositorioOcorrenciaFake()
    ).destinos([uuid4()])
    assert destinos == {}


async def test_sessao_por_tick_resolve_e_fecha():
    ocorrencias, ordens = RepositorioOcorrenciaFake(), RepositorioOrdemDespachoFake()
    o = await _ocorrencia(ocorrencias)
    viatura_id = uuid4()
    await ordens.salvar(
        OrdemDeDespacho(
            numero="OD-2026-000003",
            ocorrencia_id=o.id,
            viatura_id=viatura_id,
            operador_id=OPERADOR.id,
            criada_em=AGORA,
        )
    )
    sessoes_abertas = 0

    @asynccontextmanager
    async def fabrica() -> AsyncIterator:
        nonlocal sessoes_abertas
        sessoes_abertas += 1
        yield ordens, ocorrencias

    destinos = await ResolvedorDestinoSessao(fabrica).destinos([viatura_id])
    assert destinos == {viatura_id: DESTINO}
    assert sessoes_abertas == 1


async def test_sessao_que_falha_ao_abrir_vira_sem_destino():
    @asynccontextmanager
    async def fabrica_quebrada() -> AsyncIterator:
        raise ConnectionError("banco fora do ar")
        yield

    assert await ResolvedorDestinoSessao(fabrica_quebrada).destinos([uuid4()]) == {}
