"""Testes do value object Coordenada e do Haversine (DEC-03, DEC-05)."""
import pytest

from domain.shared.exceptions import ValorInvalidoError
from domain.shared.geo import Coordenada, calcular_distancia_km

ALEGRETE = Coordenada(-29.7833, -55.7919)
PORTO_ALEGRE = Coordenada(-30.0346, -51.2177)


def test_coordenada_valida():
    c = Coordenada(-29.78, -55.79)
    assert c.latitude == -29.78


@pytest.mark.parametrize("lat,lon", [(91, 0), (-91, 0), (0, 181), (0, -181), (float("nan"), 0)])
def test_coordenada_fora_da_faixa(lat, lon):
    with pytest.raises(ValorInvalidoError):
        Coordenada(lat, lon)


def test_coordenada_e_imutavel():
    c = Coordenada(0, 0)
    with pytest.raises(Exception):
        c.latitude = 10  # type: ignore[misc]


def test_haversine_distancia_zero():
    assert calcular_distancia_km(ALEGRETE, ALEGRETE) == 0.0


def test_haversine_alegrete_porto_alegre():
    # Distância em linha reta conhecida: ~441 km
    d = calcular_distancia_km(ALEGRETE, PORTO_ALEGRE)
    assert 435 < d < 447


def test_haversine_simetrica():
    assert calcular_distancia_km(ALEGRETE, PORTO_ALEGRE) == pytest.approx(
        calcular_distancia_km(PORTO_ALEGRE, ALEGRETE)
    )


def test_haversine_um_grau_de_latitude():
    # 1° de latitude ≈ 111,2 km
    d = calcular_distancia_km(Coordenada(0, 0), Coordenada(1, 0))
    assert d == pytest.approx(111.19, abs=0.1)
