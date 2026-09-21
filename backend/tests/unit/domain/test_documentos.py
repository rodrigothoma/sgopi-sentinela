"""Testes de validação/máscara de CPF (DEC-04, LGPD)."""
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


def test_validar_documento_aceita_rg_como_texto_livre():
    assert validar_documento("MG-12.345.678") == "MG-12.345.678"


def test_validar_documento_rejeita_cpf_invalido():
    with pytest.raises(ValorInvalidoError):
        validar_documento("123.456.789-00")


def test_mascarar_cpf():
    assert mascarar_cpf("123.456.789-09") == "***.***.789-**"
    assert mascarar_cpf("MG-12") == "***"
    assert mascarar_cpf(None) is None
