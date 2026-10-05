"""LimitadorTentativasEmMemoria (RNF02): janela deslizante, bloqueio temporário e limpeza."""
from datetime import UTC, datetime, timedelta

import pytest

from adapters.outbound.seguranca.limitador_em_memoria import LimitadorTentativasEmMemoria

T0 = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def test_bloqueia_ao_atingir_o_maximo_na_janela_e_libera_apos_o_bloqueio():
    lim = LimitadorTentativasEmMemoria(max_tentativas=3, janela_segundos=60, bloqueio_segundos=300)
    lim.registrar("a", T0)
    lim.registrar("a", T0 + timedelta(seconds=10))
    assert lim.bloqueado_ate("a", T0 + timedelta(seconds=10)) is None
    lim.registrar("a", T0 + timedelta(seconds=20))
    assert lim.bloqueado_ate("a", T0 + timedelta(seconds=21)) == T0 + timedelta(seconds=320)
    assert lim.bloqueado_ate("b", T0) is None  # chaves independentes
    assert lim.bloqueado_ate("a", T0 + timedelta(seconds=320)) is None


def test_tentativas_fora_da_janela_nao_contam():
    lim = LimitadorTentativasEmMemoria(max_tentativas=2, janela_segundos=60, bloqueio_segundos=300)
    lim.registrar("a", T0)
    lim.registrar("a", T0 + timedelta(seconds=61))
    assert lim.bloqueado_ate("a", T0 + timedelta(seconds=61)) is None


def test_limpar_zera_tentativas_e_bloqueio():
    lim = LimitadorTentativasEmMemoria(max_tentativas=1, janela_segundos=60, bloqueio_segundos=300)
    lim.registrar("a", T0)
    assert lim.bloqueado_ate("a", T0) is not None
    lim.limpar("a")
    assert lim.bloqueado_ate("a", T0) is None


@pytest.mark.parametrize("maximo,janela,bloqueio", [(0, 60, 60), (3, 0, 60), (3, 60, 0)])
def test_politica_invalida_e_recusada(maximo, janela, bloqueio):
    with pytest.raises(ValueError):
        LimitadorTentativasEmMemoria(maximo, janela, bloqueio)
