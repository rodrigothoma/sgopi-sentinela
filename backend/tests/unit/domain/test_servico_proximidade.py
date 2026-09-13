"""Serviço de domínio sugerir_viaturas_proximas com coordenadas conhecidas (RF18 aceite 1, DEC-05)."""
from datetime import UTC, datetime, timedelta

from domain.despacho.servico_proximidade import sugerir_viaturas_proximas
from domain.shared.geo import Coordenada
from domain.viatura.entity import Viatura

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
ALVO = Coordenada(-29.7833, -55.7919)  # Alegrete


def _v(prefixo, lat, lon, idade_s=0, situacao=None):
    v = Viatura(prefixo, f"P{prefixo[-2:]}0000")
    if lat is not None:
        v.registrar_posicao(Coordenada(lat, lon), AGORA - timedelta(seconds=idade_s), AGORA, 3600)
    if situacao == "despachada":
        v.despachar(AGORA)
    if situacao == "indisponivel":
        v.marcar_indisponivel(AGORA)
    return v


def test_ordena_por_distancia_e_limita_a_tres():
    frota = [
        _v("VTR-01", -29.80, -55.80),      # ~2 km
        _v("VTR-02", -29.7833, -55.7919),  # 0 km
        _v("VTR-03", -29.70, -55.70),      # ~13 km
        _v("VTR-04", -29.79, -55.79),      # ~0.8 km
    ]
    sug = sugerir_viaturas_proximas(ALVO, frota, AGORA, 60, 3)
    assert [s.viatura.prefixo for s in sug] == ["VTR-02", "VTR-04", "VTR-01"]
    assert sug[0].distancia_km == 0.0 and 0.7 < sug[1].distancia_km < 0.9 and 1.9 < sug[2].distancia_km < 2.1


def test_exclui_sem_posicao_sem_sinal_despachada_indisponivel():
    frota = [
        _v("VTR-01", None, None),
        _v("VTR-02", -29.78, -55.79, idade_s=61),
        _v("VTR-03", -29.78, -55.79, situacao="despachada"),
        _v("VTR-04", -29.78, -55.79, situacao="indisponivel"),
        _v("VTR-05", -29.78, -55.79, idade_s=60),
    ]
    sug = sugerir_viaturas_proximas(ALVO, frota, AGORA, 60, 3)
    assert [s.viatura.prefixo for s in sug] == ["VTR-05"]


def test_sem_elegiveis_devolve_lista_vazia():
    assert sugerir_viaturas_proximas(ALVO, [], AGORA, 60, 3) == []


def test_empate_desempata_por_prefixo():
    frota = [_v("VTR-09", -29.78, -55.79), _v("VTR-01", -29.78, -55.79)]
    assert [s.viatura.prefixo for s in sugerir_viaturas_proximas(ALVO, frota, AGORA, 60, 2)] == ["VTR-01", "VTR-09"]
