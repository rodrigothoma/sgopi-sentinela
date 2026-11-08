"""MaquinaEstados genérica (domain/shared)."""
from enum import Enum

from domain.shared.maquina_estados import MaquinaEstados


class Estado(Enum):
    ABERTO = "ABERTO"
    FECHADO = "FECHADO"


class Op(Enum):
    FECHAR = "fechar"
    ANOTAR = "anotar"


MAQUINA = MaquinaEstados({(Estado.ABERTO, Op.FECHAR): Estado.FECHADO, (Estado.ABERTO, Op.ANOTAR): Estado.ABERTO})


def test_proximo_e_permite():
    assert MAQUINA.proximo(Estado.ABERTO, Op.FECHAR) is Estado.FECHADO
    assert MAQUINA.proximo(Estado.FECHADO, Op.FECHAR) is None
    assert MAQUINA.permite(Estado.ABERTO, Op.ANOTAR)
    assert not MAQUINA.permite(Estado.FECHADO, Op.ANOTAR)


def test_laco_mantem_o_estado():
    assert MAQUINA.proximo(Estado.ABERTO, Op.ANOTAR) is Estado.ABERTO


def test_origens_e_destinos():
    assert MAQUINA.origens(Op.FECHAR) == {Estado.ABERTO}
    assert MAQUINA.destinos(Op.FECHAR) == {Estado.FECHADO}
