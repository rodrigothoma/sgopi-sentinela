"""Fiação do simulador com destino no Composition Root (di.montar_simulador)."""
from adapters.inbound.simulador.resolvedor_destino import ResolvedorDestinoSessao
from adapters.inbound.simulador.roteador import RoteadorLinhaReta, RoteadorOSRM
from adapters.inbound.simulador.simulador_telemetria import SimuladorTelemetria
from infrastructure.config.settings import settings
from infrastructure.di import montar_simulador


def _fabrica_dummy():
    raise AssertionError("fábrica não deve ser chamada neste teste")


def test_montar_simulador_fia_destino_com_linha_reta_por_padrao():
    sim = montar_simulador(_fabrica_dummy)
    assert isinstance(sim, SimuladorTelemetria)
    assert isinstance(sim._resolvedor, ResolvedorDestinoSessao)
    assert isinstance(sim._roteador, RoteadorLinhaReta)
    assert sim.passo_destino == settings.simulador_passo_destino_metros
    assert sim.raio_chegada == settings.simulador_raio_chegada_metros
    assert sim.jitter_chegada == settings.simulador_jitter_chegada_metros


def test_montar_simulador_usa_osrm_quando_url_configurada():
    sim = montar_simulador(_fabrica_dummy, roteador_url="http://roteador:5000")
    assert isinstance(sim._roteador, RoteadorOSRM)
