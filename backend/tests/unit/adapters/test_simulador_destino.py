"""Tick do simulador com destino (issue #54, RF02).

Fakes de ResolvedorDestino e Roteador: sem banco de ordens, sem rede.
"""
import math
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

import pytest

from adapters.inbound.simulador.resolvedor_destino import ResolvedorDestino
from adapters.inbound.simulador.roteador import ErroRoteamento, Roteador, RoteadorLinhaReta
from adapters.inbound.simulador.simulador_telemetria import SimuladorTelemetria
from application.ports.inbound.interface_gerir_viaturas import CadastrarViaturaInput
from application.use_cases.viatura.gerir_viaturas import CadastrarViatura
from application.use_cases.viatura.registrar_posicao_viatura import RegistrarPosicaoViatura
from domain.shared.geo import RAIO_TERRA_KM, Coordenada
from tests.fakes.atores import OPERADOR
from tests.fakes.portas_fake import AuditoriaFake, PublicadorEventosFake, RelogioFake, UnidadeDeTrabalhoFake
from tests.fakes.repositorio_viatura_fake import RepositorioViaturaFake
from tests.unit.use_cases.conftest import AGORA

# Alegrete/RS — sede do curso (dados fictícios, RNF10)
ORIGEM = Coordenada(-29.7833, -55.7919)
DESTINO = Coordenada(-29.7800, -55.7900)  # ~400 m da origem


class ResolvedorDestinoFake(ResolvedorDestino):
    def __init__(self, destinos: dict[UUID, Coordenada] | None = None) -> None:
        self.destinos_fixos = dict(destinos or {})

    async def destinos(self, viatura_ids: list[UUID]) -> dict[UUID, Coordenada]:
        return {vid: self.destinos_fixos[vid] for vid in viatura_ids if vid in self.destinos_fixos}


class RoteadorContador(RoteadorLinhaReta):
    def __init__(self, falhar: bool = False) -> None:
        self.chamadas = 0
        self.falhar = falhar

    def rota(self, origem: Coordenada, destino: Coordenada) -> list[Coordenada]:
        self.chamadas += 1
        if self.falhar:
            raise ErroRoteamento("falha simulada")
        return super().rota(origem, destino)


class RoteadorRotaFixa(Roteador):
    """Rota de teste terminando fora do destino bruto (OSRM ajustado à via)."""

    def __init__(self, rota: list[Coordenada]) -> None:
        self._rota = list(rota)

    def rota(self, origem: Coordenada, destino: Coordenada) -> list[Coordenada]:
        return list(self._rota)


@pytest.fixture
def repo():
    return RepositorioViaturaFake()


@pytest.fixture
def relogio():
    return RelogioFake(AGORA)


@pytest.fixture
def registrar_posicao(repo, relogio):
    return RegistrarPosicaoViatura(repo, UnidadeDeTrabalhoFake(), relogio, PublicadorEventosFake(), 60)


async def _despachada(repo, relogio, prefixo="VTR-01", placa="AAA0001"):
    v = await CadastrarViatura(repo, UnidadeDeTrabalhoFake(), relogio, AuditoriaFake(), 60).executar(
        OPERADOR, CadastrarViaturaInput(prefixo, placa)
    )
    viatura = await repo.buscar_por_id(v.id)
    viatura.registrar_posicao(ORIGEM, AGORA, AGORA, 60)
    viatura.despachar(AGORA)
    await repo.salvar(viatura)
    return viatura


def _contexto(repo, registrar_posicao):
    @asynccontextmanager
    async def contexto() -> AsyncIterator:
        yield repo, registrar_posicao

    return contexto


async def _distancia_a(repo, viatura_id, ponto: Coordenada) -> float:
    v = await repo.buscar_por_id(viatura_id)
    assert v.ultima_posicao is not None
    return v.ultima_posicao.coordenada.distancia_km(ponto) * 1000.0


async def _distancia_ao_destino(repo, viatura_id) -> float:
    return await _distancia_a(repo, viatura_id, DESTINO)


async def test_em_deslocamento_com_destino_converge_a_cada_tick(repo, relogio, registrar_posicao):
    viatura = await _despachada(repo, relogio)
    sim = SimuladorTelemetria(
        _contexto(repo, registrar_posicao),
        relogio,
        intervalo_segundos=0.01,
        raio_metros=150.0,
        semente=42,
        resolvedor=ResolvedorDestinoFake({viatura.id: DESTINO}),
        roteador=RoteadorLinhaReta(),
        passo_destino_metros=300.0,
    )
    d0 = await _distancia_ao_destino(repo, viatura.id)
    relogio.avancar(seconds=1)
    await sim.tick()
    d1 = await _distancia_ao_destino(repo, viatura.id)
    relogio.avancar(seconds=1)
    await sim.tick()
    d2 = await _distancia_ao_destino(repo, viatura.id)
    assert d1 < d0
    assert d2 < d1
    assert d2 < 10.0  # chegou: jitter de 5 m em torno do destino


async def _no_local(repo, relogio, prefixo="VTR-01", placa="AAA0001"):
    viatura = await _despachada(repo, relogio, prefixo, placa)
    viatura.chegar_ao_local(AGORA)
    await repo.salvar(viatura)
    return viatura


async def test_operando_sem_rota_em_cache_fica_onde_esta_sem_teleportar(repo, relogio, registrar_posicao):
    viatura = await _no_local(repo, relogio)
    sim = SimuladorTelemetria(
        _contexto(repo, registrar_posicao),
        relogio,
        intervalo_segundos=0.01,
        raio_metros=150.0,
        semente=42,
        resolvedor=ResolvedorDestinoFake({viatura.id: DESTINO}),
        roteador=RoteadorLinhaReta(),
    )
    relogio.avancar(seconds=1)
    await sim.tick()
    relogio.avancar(seconds=1)
    await sim.tick()
    v = await repo.buscar_por_id(viatura.id)
    assert v.ultima_posicao is not None
    assert v.ultima_posicao.coordenada.distancia_km(ORIGEM) * 1000.0 < 15.0
    assert v.ultima_posicao.coordenada.distancia_km(DESTINO) * 1000.0 > 300.0


async def test_operando_que_chegou_navegando_permanece_no_ponto(repo, relogio, registrar_posicao):
    viatura = await _despachada(repo, relogio)
    sim = SimuladorTelemetria(
        _contexto(repo, registrar_posicao),
        relogio,
        intervalo_segundos=0.01,
        raio_metros=150.0,
        semente=42,
        resolvedor=ResolvedorDestinoFake({viatura.id: DESTINO}),
        roteador=RoteadorLinhaReta(),
        passo_destino_metros=300.0,
    )
    relogio.avancar(seconds=1)
    await sim.tick()
    relogio.avancar(seconds=1)
    await sim.tick()  # chegou: jitter em torno do destino
    viatura = await repo.buscar_por_id(viatura.id)
    viatura.chegar_ao_local(relogio.agora())
    await repo.salvar(viatura)
    for _ in range(3):
        relogio.avancar(seconds=1)
        await sim.tick()
    v = await repo.buscar_por_id(viatura.id)
    assert v.ultima_posicao is not None
    assert v.ultima_posicao.coordenada.distancia_km(DESTINO) * 1000.0 < 15.0


async def test_sem_destino_mantem_passeio_aleatorio(repo, relogio, registrar_posicao):
    em_desloc = await _despachada(repo, relogio, "VTR-01", "AAA0001")
    v_disp = await CadastrarViatura(repo, UnidadeDeTrabalhoFake(), relogio, AuditoriaFake(), 60).executar(
        OPERADOR, CadastrarViaturaInput("VTR-02", "BBB0002")
    )
    disponivel = await repo.buscar_por_id(v_disp.id)
    disponivel.registrar_posicao(ORIGEM, AGORA, AGORA, 60)
    await repo.salvar(disponivel)
    sim = SimuladorTelemetria(
        _contexto(repo, registrar_posicao),
        relogio,
        intervalo_segundos=0.01,
        raio_metros=150.0,
        semente=42,
        resolvedor=ResolvedorDestinoFake({}),
        roteador=RoteadorLinhaReta(),
    )
    relogio.avancar(seconds=1)
    await sim.tick()
    for vid in (em_desloc.id, disponivel.id):
        v = await repo.buscar_por_id(vid)
        assert v.ultima_posicao is not None
        assert v.ultima_posicao.coordenada.distancia_km(ORIGEM) * 1000.0 <= 150.5
    assert await _distancia_ao_destino(repo, em_desloc.id) > 200.0  # não convergiu


D2 = Coordenada(-29.7900, -55.7950)
D3 = Coordenada(-29.7750, -55.7850)


async def test_roteador_falhando_usa_linha_reta_com_backoff(repo, relogio, registrar_posicao):
    viatura = await _despachada(repo, relogio)
    roteador = RoteadorContador(falhar=True)
    resolvedor = ResolvedorDestinoFake({viatura.id: DESTINO})
    sim = SimuladorTelemetria(
        _contexto(repo, registrar_posicao),
        relogio,
        intervalo_segundos=0.01,
        raio_metros=150.0,
        semente=42,
        resolvedor=resolvedor,
        roteador=roteador,
        passo_destino_metros=300.0,
    )
    relogio.avancar(seconds=1)
    await sim.tick()
    assert roteador.chamadas == 1
    resolvedor.destinos_fixos[viatura.id] = D2  # novo despacho: recalcula a rota
    d2_antes = (await repo.buscar_por_id(viatura.id)).ultima_posicao.coordenada.distancia_km(D2) * 1000.0
    relogio.avancar(seconds=1)
    await sim.tick()  # dentro da janela de 30 s: recalcula em linha reta, sem chamar
    assert roteador.chamadas == 1
    d2_depois = await _distancia_a(repo, viatura.id, D2)
    assert d2_depois < d2_antes
    resolvedor.destinos_fixos[viatura.id] = D3
    d3_antes = (await repo.buscar_por_id(viatura.id)).ultima_posicao.coordenada.distancia_km(D3) * 1000.0
    relogio.avancar(seconds=31)
    await sim.tick()  # janela expirou: retenta o roteador (e falha de novo)
    assert roteador.chamadas == 2
    assert await _distancia_a(repo, viatura.id, D3) < d3_antes


async def test_novo_destino_recalcula_a_rota(repo, relogio, registrar_posicao):
    viatura = await _despachada(repo, relogio)
    roteador = RoteadorContador()
    resolvedor = ResolvedorDestinoFake({viatura.id: DESTINO})
    sim = SimuladorTelemetria(
        _contexto(repo, registrar_posicao),
        relogio,
        intervalo_segundos=0.01,
        raio_metros=150.0,
        semente=42,
        resolvedor=resolvedor,
        roteador=roteador,
        passo_destino_metros=300.0,
    )
    relogio.avancar(seconds=1)
    await sim.tick()
    assert roteador.chamadas == 1
    resolvedor.destinos_fixos[viatura.id] = D2
    d_antes = (await repo.buscar_por_id(viatura.id)).ultima_posicao.coordenada.distancia_km(D2) * 1000.0
    relogio.avancar(seconds=1)
    await sim.tick()
    assert roteador.chamadas == 2  # destino mudou: rota recalculada
    assert await _distancia_a(repo, viatura.id, D2) < d_antes  # converge ao novo destino


async def test_perdeu_destino_descarta_rota_em_cache(repo, relogio, registrar_posicao):
    viatura = await _despachada(repo, relogio)
    roteador = RoteadorContador()
    resolvedor = ResolvedorDestinoFake({viatura.id: DESTINO})
    sim = SimuladorTelemetria(
        _contexto(repo, registrar_posicao),
        relogio,
        intervalo_segundos=0.01,
        raio_metros=150.0,
        semente=42,
        resolvedor=resolvedor,
        roteador=roteador,
        passo_destino_metros=300.0,
    )
    relogio.avancar(seconds=1)
    await sim.tick()
    assert roteador.chamadas == 1
    del resolvedor.destinos_fixos[viatura.id]  # ordem encerrada: perdeu o destino
    relogio.avancar(seconds=1)
    await sim.tick()
    assert sim._rotas == {}
    resolvedor.destinos_fixos[viatura.id] = DESTINO
    relogio.avancar(seconds=1)
    await sim.tick()
    assert roteador.chamadas == 2  # cache descartado: rota recalculada


async def test_backoff_do_roteador_e_global_nao_por_viatura(repo, relogio, registrar_posicao):
    v1 = await _despachada(repo, relogio, "VTR-01", "AAA0001")
    v2 = await _despachada(repo, relogio, "VTR-02", "BBB0002")
    roteador = RoteadorContador(falhar=True)
    sim = SimuladorTelemetria(
        _contexto(repo, registrar_posicao),
        relogio,
        intervalo_segundos=0.01,
        raio_metros=150.0,
        semente=42,
        resolvedor=ResolvedorDestinoFake({v1.id: DESTINO, v2.id: D2}),
        roteador=roteador,
        passo_destino_metros=300.0,
    )
    relogio.avancar(seconds=1)
    await sim.tick()
    assert roteador.chamadas == 2  # uma por viatura sem cache
    relogio.avancar(seconds=1)
    await sim.tick()
    assert roteador.chamadas == 2  # backoff global: nenhuma retentativa dentro da janela


async def test_jitter_centrado_no_ultimo_ponto_da_rota(repo, relogio, registrar_posicao):
    delta_30m = 30.0 / (RAIO_TERRA_KM * 1000.0) * 180.0 / math.pi
    ajustado = Coordenada(DESTINO.latitude - delta_30m, DESTINO.longitude)  # OSRM ajustou à via
    viatura = await _despachada(repo, relogio)
    sim = SimuladorTelemetria(
        _contexto(repo, registrar_posicao),
        relogio,
        intervalo_segundos=0.01,
        raio_metros=150.0,
        semente=42,
        resolvedor=ResolvedorDestinoFake({viatura.id: DESTINO}),
        roteador=RoteadorRotaFixa([ORIGEM, ajustado]),
        passo_destino_metros=300.0,
    )
    relogio.avancar(seconds=1)
    await sim.tick()
    relogio.avancar(seconds=1)
    await sim.tick()  # chegou ao último ponto: jitter
    relogio.avancar(seconds=1)
    await sim.tick()
    v = await repo.buscar_por_id(viatura.id)
    assert v.ultima_posicao is not None
    assert v.ultima_posicao.coordenada.distancia_km(ajustado) * 1000.0 < 10.0
    assert 20.0 < v.ultima_posicao.coordenada.distancia_km(DESTINO) * 1000.0 < 40.0
