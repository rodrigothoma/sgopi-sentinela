"""Chave pública de autenticidade e situação do documento emitido (RF08 / UC08) — puro domínio."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from domain.ocorrencia.autenticidade import (
    ALFABETO_CHAVE,
    TAMANHO_CHAVE,
    SituacaoDocumento,
    formatar_chave,
    gerar_chave_autenticidade,
    normalizar_chave,
)
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipoEnvolvido
from domain.shared.exceptions import ValorInvalidoError
from domain.shared.geo import Coordenada

AGORA = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
AGENTE = uuid4()
DELEGADO = uuid4()


def _registrar() -> Ocorrencia:
    return Ocorrencia.registrar(
        agente_policial_id=AGENTE,
        natureza="Furto",
        descricao="Furto de veículo na rua X, próximo à praça central.",
        localizacao="Rua X, 100",
        coordenada=Coordenada(-29.78, -55.79),
        data_hora_fato=AGORA - timedelta(hours=1),
        numero_protocolo="SGOPI-2026-000001",
        agora=AGORA,
        envolvidos=[Envolvido(nome="João", tipo=TipoEnvolvido.VITIMA)],
    )


# ------------------------------------------------------------------- chave
def test_chave_tem_24_caracteres_do_alfabeto_sem_ambiguidade():
    chave = gerar_chave_autenticidade()
    assert len(chave) == TAMANHO_CHAVE == 24
    assert all(c in ALFABETO_CHAVE for c in chave)
    assert not set("0O1I") & set(ALFABETO_CHAVE)


def test_chaves_geradas_sao_unicas():
    assert len({gerar_chave_autenticidade() for _ in range(200)}) == 200


def test_normalizar_aceita_hifens_espacos_e_minusculas():
    chave = gerar_chave_autenticidade()
    digitada = f" {formatar_chave(chave).lower()} "
    assert normalizar_chave(digitada) == chave


def test_formatar_agrupa_de_4_em_4():
    chave = "ABCD" * 6
    assert formatar_chave(chave) == "ABCD-ABCD-ABCD-ABCD-ABCD-ABCD"


@pytest.mark.parametrize("invalida", ["", None, "ABC", "A" * 23, "A" * 25, "0000" * 6, "ABCD" * 5 + "ABC!"])
def test_normalizar_rejeita_chave_malformada(invalida):
    with pytest.raises(ValorInvalidoError) as exc:
        normalizar_chave(invalida)
    assert exc.value.chave == "documento.chave_invalida"


# ---------------------------------------------------------------- entidade
def test_ocorrencia_registrada_nao_tem_documento_emitido():
    o = _registrar()
    assert o.chave_autenticidade is None
    assert o.situacao_documento() is None
    assert o.emitida_em() is None


def test_validacao_emite_documento_com_chave_e_situacao_valida():
    o = _registrar()
    validada_em = AGORA + timedelta(minutes=5)
    o.validar(DELEGADO, validada_em)
    assert o.chave_autenticidade is not None and len(o.chave_autenticidade) == TAMANHO_CHAVE
    assert o.situacao_documento() is SituacaoDocumento.VALIDO
    assert o.emitida_em() == validada_em


def test_adulteracao_apos_emissao_e_detectada():
    o = _registrar()
    o.validar(DELEGADO, AGORA)
    o.descricao = "Narrativa alterada diretamente no banco após a validação."
    assert o.narrativa_integra() is False
    assert o.situacao_documento() is SituacaoDocumento.ADULTERADO


def test_rejeicao_nao_emite_documento():
    o = _registrar()
    o.rejeitar(DELEGADO, "Fato atípico e sem materialidade.", AGORA)
    assert o.chave_autenticidade is None and o.situacao_documento() is None
