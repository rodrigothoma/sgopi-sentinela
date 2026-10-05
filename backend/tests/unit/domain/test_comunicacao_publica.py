"""Regras do canal público (RF01 — Delegacia Online): maioridade declarada e CPF conferido."""
import pytest

from domain.ocorrencia.comunicacao_publica import validar_comunicacao_publica
from domain.shared.exceptions import ValorInvalidoError


@pytest.mark.parametrize("documento", ["529.982.247-25", "52998224725", "1234567890"])
def test_aceita_cpf_valido_e_rg(documento):
    validar_comunicacao_publica(documento, declaracao_maioridade=True)


def test_exige_declaracao_de_maioridade():
    with pytest.raises(ValorInvalidoError) as exc:
        validar_comunicacao_publica("52998224725", declaracao_maioridade=False)
    assert exc.value.chave == "ocorrencia.declaracao_maioridade_ausente"


@pytest.mark.parametrize("documento", ["111.111.111-11", "52998224724"])
def test_recusa_cpf_invalido(documento):
    with pytest.raises(ValorInvalidoError) as exc:
        validar_comunicacao_publica(documento, declaracao_maioridade=True)
    assert exc.value.chave == "envolvido.cpf_comunicante_invalido"
