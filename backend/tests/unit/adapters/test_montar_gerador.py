"""Issue #55: fiação do gerador no Composition Root (di.montar_gerador)."""
from adapters.inbound.simulador.gerador_ocorrencias import GeradorOcorrencias
from infrastructure.config.settings import settings
from infrastructure.di import montar_gerador


def _fabrica_dummy():
    raise AssertionError("fábrica não deve ser chamada neste teste")


def test_montar_gerador_usa_intervalo_do_settings():
    gen = montar_gerador(_fabrica_dummy)
    assert isinstance(gen, GeradorOcorrencias)
    assert gen.intervalo == settings.gerador_ocorrencias_intervalo_segundos
    assert gen.ligado is False
