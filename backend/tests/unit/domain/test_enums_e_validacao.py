"""Helpers de domínio: interpretar_enum, interpretar_enum_ou_padrao e exigir_texto."""
from enum import Enum

import pytest

from domain.shared.enums import interpretar_enum, interpretar_enum_ou_padrao
from domain.shared.exceptions import CampoObrigatorioError, ValorInvalidoError
from domain.shared.validacao import exigir_texto


class Cor(str, Enum):
    AZUL = "AZUL"
    VERDE = "VERDE"


def test_interpretar_enum_exato_por_padrao():
    assert interpretar_enum(Cor, "AZUL", "cor.invalida") is Cor.AZUL
    with pytest.raises(ValorInvalidoError):
        interpretar_enum(Cor, "azul", "cor.invalida")


def test_interpretar_enum_normalizado_e_mensagem():
    assert interpretar_enum(Cor, " verde ", "cor.invalida", normalizar=True) is Cor.VERDE
    with pytest.raises(ValorInvalidoError) as erro:
        interpretar_enum(Cor, "roxo", "cor.invalida", "Cor inválida: {valor}")
    assert erro.value.chave == "cor.invalida" and str(erro.value) == "Cor inválida: roxo"


def test_interpretar_enum_aceita_o_proprio_membro():
    assert interpretar_enum(Cor, Cor.AZUL, "cor.invalida") is Cor.AZUL


def test_interpretar_enum_ou_padrao():
    assert interpretar_enum_ou_padrao(Cor, "verde", Cor.AZUL) is Cor.VERDE
    assert interpretar_enum_ou_padrao(Cor, "roxo", Cor.AZUL) is Cor.AZUL
    assert interpretar_enum_ou_padrao(Cor, None, Cor.AZUL) is Cor.AZUL


def test_exigir_texto_devolve_sem_bordas():
    assert exigir_texto("  Maria  ", "Nome obrigatório.") == "Maria"


@pytest.mark.parametrize("valor", [None, "", "   "])
def test_exigir_texto_recusa_vazio(valor):
    with pytest.raises(CampoObrigatorioError) as erro:
        exigir_texto(valor, "Nome obrigatório.", chave="pessoa.nome_vazio")
    assert erro.value.chave == "pessoa.nome_vazio"


def test_exigir_texto_minimo_e_tipo_de_erro():
    with pytest.raises(ValorInvalidoError):
        exigir_texto("curto", "Mínimo de 10.", minimo=10, erro=ValorInvalidoError)
