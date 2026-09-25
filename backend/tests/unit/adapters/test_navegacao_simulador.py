"""Navegação do simulador com destino (issue #54, RF02).

Função pura: sem banco, sem rede, sem Roteador real.
"""
import math

from domain.shared.geo import RAIO_TERRA_KM, Coordenada
from adapters.inbound.simulador.navegacao import avancar_na_rota

# Alegrete/RS — sede do curso (dados fictícios, RNF10)
ALEGRETE = Coordenada(-29.7833, -55.7919)
DESTINO = Coordenada(-29.7800, -55.7900)  # ~400 m do centro


def test_rota_vazia_mantem_posicao_e_nao_chega_quando_longe():
    resultado = avancar_na_rota(
        ALEGRETE, DESTINO, [], indice=0, passo_max_metros=300.0, raio_chegada_metros=50.0
    )
    assert resultado.nova_posicao == ALEGRETE
    assert resultado.indice_rota == 0
    assert resultado.chegou is False


def test_rota_de_um_ponto_mantem_posicao():
    longe = avancar_na_rota(
        ALEGRETE, DESTINO, [ALEGRETE], indice=0, passo_max_metros=300.0, raio_chegada_metros=50.0
    )
    assert longe.nova_posicao == ALEGRETE
    assert longe.chegou is False
    perto = avancar_na_rota(
        ponto_a_sul(49.9), DESTINO, [DESTINO], indice=0, passo_max_metros=300.0, raio_chegada_metros=50.0
    )
    assert perto.nova_posicao == ponto_a_sul(49.9)
    assert perto.chegou is True


def test_passo_maior_que_distancia_fixa_no_destino_sem_ultrapassar():
    atual = Coordenada(DESTINO.latitude - 0.0009, DESTINO.longitude)  # ~100 m ao sul
    resultado = avancar_na_rota(
        atual, DESTINO, [atual, DESTINO], indice=0, passo_max_metros=300.0, raio_chegada_metros=50.0
    )
    assert resultado.nova_posicao == DESTINO
    assert resultado.chegou is True


def ponto_a_sul(metros: float) -> Coordenada:
    """Ponto exatamente ``metros`` ao sul do destino (mesmo elipsoide do Haversine)."""
    delta_graus = metros / (RAIO_TERRA_KM * 1000.0) * 180.0 / math.pi
    return Coordenada(DESTINO.latitude - delta_graus, DESTINO.longitude)


def test_chegada_usa_menor_estrito_49m9_sim_50m1_nao():
    dentro = avancar_na_rota(
        ponto_a_sul(49.9), DESTINO, [], indice=0, passo_max_metros=300.0, raio_chegada_metros=50.0
    )
    assert dentro.nova_posicao == ponto_a_sul(49.9)
    assert dentro.chegou is True
    fora = avancar_na_rota(
        ponto_a_sul(50.1), DESTINO, [], indice=0, passo_max_metros=300.0, raio_chegada_metros=50.0
    )
    assert fora.nova_posicao == ponto_a_sul(50.1)
    assert fora.chegou is False


def test_distancia_zero_chega_sem_divisao_por_zero():
    meio = ponto_a_sul(200.0)
    resultado = avancar_na_rota(
        DESTINO, DESTINO, [meio, DESTINO], indice=0, passo_max_metros=300.0, raio_chegada_metros=50.0
    )
    assert resultado.nova_posicao == DESTINO
    assert resultado.chegou is True


def test_avanco_encadeado_ao_longo_de_varios_pontos():
    origem = ponto_a_sul(800.0)
    meio = ponto_a_sul(450.0)
    rota = [origem, meio, DESTINO]
    kwargs = {"destino": DESTINO, "rota": rota, "passo_max_metros": 300.0, "raio_chegada_metros": 50.0}

    tick1 = avancar_na_rota(origem, indice=0, **kwargs)
    assert 499.0 < tick1.nova_posicao.distancia_km(DESTINO) * 1000.0 < 501.0
    assert tick1.indice_rota == 0
    assert tick1.chegou is False

    tick2 = avancar_na_rota(tick1.nova_posicao, indice=tick1.indice_rota, **kwargs)
    assert 199.0 < tick2.nova_posicao.distancia_km(DESTINO) * 1000.0 < 201.0
    assert tick2.indice_rota == 1
    assert tick2.chegou is False

    tick3 = avancar_na_rota(tick2.nova_posicao, indice=tick2.indice_rota, **kwargs)
    assert tick3.nova_posicao == DESTINO
    assert tick3.chegou is True
