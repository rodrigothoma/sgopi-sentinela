"""Testes do driving adapter OrquestradorDespacho (Issues #62/#63)."""
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from adapters.inbound.simulador.orquestrador_despacho import (
    OBSERVACOES_DESPACHO,
    OrquestradorDespacho,
)
from application.ports.inbound.ator import Ator
from application.use_cases.despacho.despachar_viatura import DespacharViatura
from application.use_cases.despacho.encerrar_ocorrencia import EncerrarOcorrencia
from domain.ocorrencia.entity import Ocorrencia
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.geo import Coordenada
from domain.usuario.entity import Papel
from domain.viatura.entity import Posicao, SituacaoViatura, Viatura
from tests.fakes.despacho_fake import GeradorNumeroOrdemFake, RepositorioOrdemDespachoFake
from tests.fakes.portas_fake import AuditoriaFake, PublicadorEventosFake, RelogioFake, UnidadeDeTrabalhoFake
from tests.fakes.repositorio_ocorrencia_fake import RepositorioOcorrenciaFake
from tests.fakes.repositorio_viatura_fake import RepositorioViaturaFake

AGORA = datetime(2026, 9, 20, 14, 0, tzinfo=UTC)

OPERADOR_SIMULADOR = Ator(id=UUID("00000000-0000-0000-0000-000000000005"), login="simulador-operador", papel=Papel.OPERADOR_CENTRAL)
DELEGADO_SIMULADOR = Ator(id=UUID("00000000-0000-0000-0000-000000000006"), login="simulador-delegado", papel=Papel.DELEGADO)


class _Ambiente:
    """Fakes + casos de uso REAIS (mesmo contrato do DI), com relógio único."""

    def __init__(self, com_atores: bool = True, relogio: RelogioFake | None = None) -> None:
        self.relogio = relogio or RelogioFake(AGORA)
        self.viaturas = RepositorioViaturaFake()
        self.ocorrencias = RepositorioOcorrenciaFake()
        self.ordens = RepositorioOrdemDespachoFake()
        self._uow = UnidadeDeTrabalhoFake()
        self.auditoria = AuditoriaFake()
        self.publicador = PublicadorEventosFake()
        self.operador = OPERADOR_SIMULADOR if com_atores else None
        self.delegado = DELEGADO_SIMULADOR if com_atores else None
        self._despachar = DespacharViatura(
            self.ocorrencias, self.viaturas, self.ordens, GeradorNumeroOrdemFake(),
            self._uow, self.relogio, self.auditoria, self.publicador,
        )
        self._encerrar = EncerrarOcorrencia(
            self.ocorrencias, self.viaturas, self.ordens, self._uow, self.relogio, self.auditoria, self.publicador,
        )

    @asynccontextmanager
    async def contexto(self):
        yield (self.viaturas, self.ocorrencias, self.ordens, self._despachar, self._encerrar, self.operador, self.delegado)

    def orquestrador(self, **kw) -> OrquestradorDespacho:
        defaults = dict(
            intervalo_segundos=10.0, janela_carencia_segundos=20, tempo_atendimento_segundos=45, max_idade_segundos=60,
        )
        defaults.update(kw)
        return OrquestradorDespacho(self.contexto, self.relogio, **defaults)


def _ocorrencia(validada_em: datetime, id: UUID | None = None, lat: float = -29.78, lng: float = -55.79) -> Ocorrencia:
    return Ocorrencia(
        id=id or uuid4(),
        agente_policial_id=uuid4(),
        natureza="Furto",
        descricao="Bem subtraído em via pública.",
        localizacao="Av. Brasil, 500",
        coordenada=Coordenada(lat, lng),
        data_hora_fato=AGORA - timedelta(hours=2),
        numero_protocolo=f"2026.01.{uuid4().hex[:6]}",
        criada_em=AGORA - timedelta(hours=2),
        status=StatusOcorrencia.VALIDADA,
        atualizada_em=validada_em,
    )


def _viatura(prefixo: str, lat: float = -29.78, lng: float = -55.79, gps_em: datetime | None = None, situacao: SituacaoViatura = SituacaoViatura.DISPONIVEL) -> Viatura:
    return Viatura(
        prefixo=prefixo,
        placa=f"ABC-{prefixo.replace('-', '')[-4:]}",
        situacao=situacao,
        ultima_posicao=Posicao(Coordenada(lat, lng), gps_em or AGORA),
    )


async def _guardar(env: _Ambiente, *entidades) -> None:
    for e in entidades:
        repo = env.viaturas if isinstance(e, Viatura) else env.ocorrencias
        await repo.salvar(e)


async def test_intervalo_menor_que_1s_e_rejeitado():
    with pytest.raises(ValueError):
        _Ambiente().orquestrador(intervalo_segundos=0.5)


async def test_ligar_sem_atores_do_seed_loga_e_nao_inicia(caplog):
    env = _Ambiente(com_atores=False)
    with caplog.at_level(logging.WARNING):
        assert await env.orquestrador().ligar() is False
    assert "rode o seed" in caplog.text
    assert not env.orquestrador().ligado


async def test_carencia_nao_cumprida_nao_despacha():
    env = _Ambiente()
    await _guardar(env, _ocorrencia(validada_em=AGORA), _viatura("VTR-01"))
    orq = env.orquestrador()
    await orq.tick()
    assert orq.despachados == 0
    assert orq.ocioso == 1


async def test_sem_viatura_nenhum_despacho():
    env = _Ambiente()
    await _guardar(env, _ocorrencia(validada_em=AGORA - timedelta(minutes=5)))
    orq = env.orquestrador()
    await orq.tick()
    assert orq.despachados == 0
    assert (await env.ordens.listar(somente_ativas=True)) == []


async def test_viatura_com_gps_vencido_nao_e_despachada():
    env = _Ambiente()
    vencida = AGORA - timedelta(seconds=120)  # max_idade default 60s
    await _guardar(env, _ocorrencia(validada_em=AGORA - timedelta(minutes=5)), _viatura("VTR-01", gps_em=vencida))
    orq = env.orquestrador()
    await orq.tick()
    assert orq.despachados == 0
    v = await env.viaturas.buscar_por_prefixo("VTR-01")
    assert v.situacao == SituacaoViatura.DISPONIVEL


async def test_despacho_feliz_usa_ator_operador():
    env = _Ambiente()
    ocorrencia = _ocorrencia(validada_em=AGORA - timedelta(minutes=5))
    await _guardar(env, ocorrencia, _viatura("VTR-01"))
    orq = env.orquestrador()
    await orq.tick()
    assert orq.despachados == 1
    assert env.auditoria.operacoes() == ["despacho.criar"]
    o = await env.ocorrencias.buscar_por_id(ocorrencia.id)
    assert o.status == StatusOcorrencia.EM_ATENDIMENTO
    v = await env.viaturas.buscar_por_prefixo("VTR-01")
    assert v.situacao == SituacaoViatura.EM_DESLOCAMENTO
    ativas = await env.ordens.listar(somente_ativas=True)
    assert len(ativas) == 1
    assert ativas[0].observacoes == OBSERVACOES_DESPACHO


async def test_unicidade_uma_viatura_para_duas_ocorrencias():
    env = _Ambiente()
    o1 = _ocorrencia(validada_em=AGORA - timedelta(minutes=5))
    o2 = _ocorrencia(validada_em=AGORA - timedelta(minutes=5))
    await _guardar(env, o1, o2, _viatura("VTR-01"))
    orq = env.orquestrador()
    await orq.tick()
    assert orq.despachados == 1
    assert len(await env.ordens.listar(somente_ativas=True)) == 1
    v = await env.viaturas.buscar_por_prefixo("VTR-01")
    assert v.situacao == SituacaoViatura.EM_DESLOCAMENTO


async def test_chegada_observada_sem_encerrar_antes_do_prazo():
    env = _Ambiente()
    ocorrencia = _ocorrencia(validada_em=AGORA - timedelta(minutes=5))
    await _guardar(env, ocorrencia, _viatura("VTR-01"))
    orq = env.orquestrador()
    await orq.tick()
    v = await env.viaturas.buscar_por_prefixo("VTR-01")
    v.chegar_ao_local(env.relogio.agora())
    await env.viaturas.salvar(v)
    await orq.tick()
    assert orq.encerrados == 0
    assert orq.ticks == 2
    o = await env.ocorrencias.buscar_por_id(ocorrencia.id)
    assert o.status == StatusOcorrencia.EM_ATENDIMENTO


async def test_encerramento_no_prazo_usa_ator_delegado():
    env = _Ambiente()
    ocorrencia = _ocorrencia(validada_em=AGORA - timedelta(minutes=5))
    await _guardar(env, ocorrencia, _viatura("VTR-01"))
    orq = env.orquestrador()
    await orq.tick()
    v = await env.viaturas.buscar_por_prefixo("VTR-01")
    v.chegar_ao_local(env.relogio.agora())
    await env.viaturas.salvar(v)
    await orq.tick()
    env.relogio.avancar(seconds=46)
    await orq.tick()
    assert orq.encerrados == 1
    o = await env.ocorrencias.buscar_por_id(ocorrencia.id)
    assert o.status == StatusOcorrencia.ENCERRADA
    assert "Atendimento simulado" in o.desfecho
    v = await env.viaturas.buscar_por_prefixo("VTR-01")
    assert v.situacao == SituacaoViatura.DISPONIVEL
    assert await env.ordens.buscar_ativa_por_viatura(v.id) is None
    assert "ocorrencia.encerrar" in env.auditoria.operacoes()


async def test_tick_nao_derruba_quando_contexto_falha(caplog):
    @asynccontextmanager
    async def contexto_falho():
        raise RuntimeError("banco caiu")
        yield  # pragma: no cover

    env = _Ambiente()
    orq = OrquestradorDespacho(contexto_falho, env.relogio, intervalo_segundos=10.0)
    with caplog.at_level(logging.WARNING):
        await orq.tick()
    assert orq.ticks == 1
    assert orq.ocioso == 1