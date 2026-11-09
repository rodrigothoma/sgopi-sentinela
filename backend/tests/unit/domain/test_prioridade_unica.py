"""Ocorrências e ofícios compartilham a mesma escala de prioridade."""
from domain.interagencias.entity import PrioridadeComunicacao
from domain.ocorrencia.prioridade import PrioridadeOcorrencia
from domain.shared.prioridade import Prioridade


def test_ocorrencia_e_oficio_usam_o_mesmo_enum():
    assert PrioridadeOcorrencia is Prioridade and PrioridadeComunicacao is Prioridade
    assert [p.peso for p in Prioridade] == [1, 2, 3, 4]
