"""Roteamento do simulador com destino (issue #54, RF02).

Sem rede nos testes: o ``RoteadorOSRM`` recebe a função de busca injetável.
"""
import pytest

from domain.shared.geo import Coordenada
from adapters.inbound.simulador.roteador import ErroRoteamento, RoteadorLinhaReta, RoteadorOSRM

# Alegrete/RS — sede do curso (dados fictícios, RNF10)
ORIGEM = Coordenada(-29.7833, -55.7919)
DESTINO = Coordenada(-29.7800, -55.7900)

# Resposta fixa do OSRM (route/v1/driving com geometries=geojson):
# pares na ordem [longitude, latitude].
RESPOSTA_OSRM = {
    "code": "Ok",
    "routes": [
        {
            "distance": 412.7,
            "duration": 95.0,
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-55.7919, -29.7833],
                    [-55.7910, -29.7820],
                    [-55.7900, -29.7800],
                ],
            },
        }
    ],
}


def buscar_fixa(url: str) -> dict:
    assert url.startswith("http://roteador:5000/route/v1/driving/")
    assert "overview=full" in url and "geometries=geojson" in url
    return RESPOSTA_OSRM


def test_osrm_converte_pares_lon_lat_para_coordenada():
    roteador = RoteadorOSRM("http://roteador:5000", buscar=buscar_fixa)
    rota = roteador.rota(ORIGEM, DESTINO)
    assert rota == [
        Coordenada(-29.7833, -55.7919),
        Coordenada(-29.7820, -55.7910),
        Coordenada(-29.7800, -55.7900),
    ]


def test_linha_reta_devolve_sempre_origem_e_destino():
    assert RoteadorLinhaReta().rota(ORIGEM, DESTINO) == [ORIGEM, DESTINO]
    assert RoteadorLinhaReta().rota(DESTINO, DESTINO) == [DESTINO, DESTINO]


def test_osrm_sem_rota_ou_codigo_erro_vira_erro_roteamento():
    for resposta in ({"code": "Ok", "routes": []}, {"code": "NoRoute", "routes": []}, {}):
        with pytest.raises(ErroRoteamento):
            RoteadorOSRM("http://roteador:5000", buscar=lambda url: resposta).rota(ORIGEM, DESTINO)


def test_osrm_falha_de_rede_vira_erro_roteamento():
    def rede_fora(url: str) -> dict:
        raise ConnectionError("roteador fora do ar")

    with pytest.raises(ErroRoteamento):
        RoteadorOSRM("http://roteador:5000", buscar=rede_fora).rota(ORIGEM, DESTINO)
