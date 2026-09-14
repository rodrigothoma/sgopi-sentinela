"""Testes de validação/máscara de CPF (DEC-04, RNF10)."""
import pytest

from domain.shared.documentos import cpf_valido, mascarar_cpf, validar_documento
from domain.shared.exceptions import ValorInvalidoError


def test_cpf_valido():
    assert cpf_valido("123.456.789-09")
    assert cpf_valido("52998224725")


def test_cpf_invalido():
    assert not cpf_valido("123.456.789-00")
    assert not cpf_valido("111.111.111-11")
    assert not cpf_valido("123")


def test_validar_documento_aceita_none_e_vazio():
    assert validar_documento(None) is None
    assert validar_documento("   ") is None


@pytest.mark.parametrize("rg", ["1234567890", "123.456.789-0", "1 234 567 890"])
def test_validar_documento_aceita_rg_com_exatamente_10_digitos(rg):
    assert validar_documento(rg) == rg


@pytest.mark.parametrize("valor", ["MG-12.345.678", "12.345.678-X", "abc", "１２３４５"])
def test_validar_documento_rejeita_letras(valor):
    with pytest.raises(ValorInvalidoError) as exc:
        validar_documento(valor)
    assert exc.value.chave == "envolvido.documento_nao_numerico"


@pytest.mark.parametrize("valor", ["123456789", "12345", "123456789012", "1"])
def test_validar_documento_rejeita_tamanho_diferente_de_10_ou_11(valor):
    with pytest.raises(ValorInvalidoError) as exc:
        validar_documento(valor)
    assert exc.value.chave == "envolvido.documento_tamanho_invalido"


@pytest.mark.parametrize("cpf", ["123.456.789-00", "12345678900", "111.111.111-11", "123.456.789-09"])
def test_validar_documento_aceita_cpf_com_11_digitos_sem_conferir_verificadores(cpf):
    assert validar_documento(cpf) == cpf


def test_mascarar_cpf():
    assert mascarar_cpf("123.456.789-09") == "***.***.789-**"
    assert mascarar_cpf("MG-12") == "***"
    assert mascarar_cpf(None) is None
