"""Entidade Viatura: máquina de estados, janela de telemetria, sinal (RF15, RF16, RNF04*)."""
from datetime import UTC, datetime, timedelta

import pytest

from domain.shared.exceptions import CampoObrigatorioError, TransicaoInvalidaError, ValorInvalidoError
from domain.shared.geo import Coordenada
from domain.viatura.entity import SituacaoViatura, Viatura

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
C = Coordenada(-29.78, -55.79)


def test_normaliza_prefixo_e_placa():
    v = Viatura(prefixo=" vtr-01 ", placa="iab 1a23")
    assert v.prefixo == "VTR-01" and v.placa == "IAB1A23" and v.situacao == SituacaoViatura.DISPONIVEL


@pytest.mark.parametrize("kw", [dict(prefixo="", placa="X"), dict(prefixo="X", placa=" ")])
def test_campos_obrigatorios(kw):
    with pytest.raises(CampoObrigatorioError):
        Viatura(**kw)


def test_registrar_posicao_dentro_da_janela():
    v = Viatura("VTR-01", "AAA1111")
    v.registrar_posicao(C, AGORA - timedelta(seconds=30), AGORA, 60)
    assert v.ultima_posicao.coordenada == C and v.sinal(AGORA, 60) == "OK"


@pytest.mark.parametrize("desvio", [61, -61, 3600])
def test_posicao_fora_da_janela_e_rejeitada_e_anterior_mantida(desvio):
    v = Viatura("VTR-01", "AAA1111")
    v.registrar_posicao(C, AGORA, AGORA, 60)
    with pytest.raises(ValorInvalidoError) as exc:
        v.registrar_posicao(Coordenada(0, 0), AGORA + timedelta(seconds=desvio), AGORA, 60)
    assert exc.value.chave == "telemetria.timestamp_fora_da_janela"
    assert v.ultima_posicao.coordenada == C  # RNF04*


def test_posicao_retroativa_rejeitada():
    v = Viatura("VTR-01", "AAA1111")
    v.registrar_posicao(C, AGORA, AGORA, 60)
    with pytest.raises(ValorInvalidoError):
        v.registrar_posicao(C, AGORA - timedelta(seconds=10), AGORA, 60)


def test_posicao_sem_fuso_rejeitada():
    with pytest.raises(ValorInvalidoError):
        Viatura("VTR-01", "AAA1111").registrar_posicao(C, datetime(2026, 9, 13, 12), AGORA, 60)


def test_sinal_sem_posicao_e_sem_sinal():
    v = Viatura("VTR-01", "AAA1111")
    assert v.sinal(AGORA, 60) == "SEM_POSICAO" and not v.posicao_valida(AGORA, 60)
    v.registrar_posicao(C, AGORA, AGORA, 60)
    assert v.sinal(AGORA + timedelta(seconds=61), 60) == "SEM_SINAL"
    assert v.sinal(AGORA + timedelta(seconds=60), 60) == "OK"


def test_ciclo_despacho_liberacao():
    v = Viatura("VTR-01", "AAA1111")
    v.despachar(AGORA)
    assert v.situacao == SituacaoViatura.EM_DESLOCAMENTO and not v.despachavel and v.versao == 2
    with pytest.raises(TransicaoInvalidaError):
        v.marcar_indisponivel(AGORA)  # RF15 aceite 2
    with pytest.raises(TransicaoInvalidaError):
        v.despachar(AGORA)
    v.chegar_ao_local(AGORA)
    assert v.situacao == SituacaoViatura.OPERANDO
    v.liberar(AGORA)
    assert v.situacao == SituacaoViatura.DISPONIVEL and v.despachavel


def test_indisponivel_manual():
    v = Viatura("VTR-01", "AAA1111")
    v.marcar_indisponivel(AGORA)
    with pytest.raises(TransicaoInvalidaError):
        v.despachar(AGORA)
    with pytest.raises(TransicaoInvalidaError):
        v.marcar_indisponivel(AGORA)
    v.marcar_disponivel(AGORA)
    assert v.despachavel
