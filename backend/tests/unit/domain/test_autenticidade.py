"""Testes unitários da autenticidade pública do documento (RF08 / UC08) — Python puro."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from domain.ocorrencia.autenticidade import (
    ALFABETO_CHAVE,
    TAMANHO_CHAVE,
    SituacaoDocumento,
    TipoCodigoVerificacao,
    formatar_chave,
    gerar_chave_autenticidade,
    interpretar_codigo,
)
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipoEnvolvido
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import ValorInvalidoError
from domain.shared.geo import Coordenada

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
AGENTE = uuid4()
DELEGADO = uuid4()
CHAVE = "ABCD" * 6
HASH = "ab" * 32


def _registrada() -> Ocorrencia:
    return Ocorrencia.registrar(
        agente_policial_id=AGENTE,
        natureza="Furto",
        descricao="Furto de veículo na rua X, próximo à praça central.",
        localizacao="Rua das Flores, 123",
        coordenada=Coordenada(-29.78, -55.79),
        data_hora_fato=AGORA - timedelta(hours=1),
        numero_protocolo="SGOPI-2026-000001",
        agora=AGORA,
        envolvidos=[Envolvido(nome="João Silva", tipo=TipoEnvolvido.VITIMA)],
    )


def _validada() -> Ocorrencia:
    o = _registrada()
    o.validar(DELEGADO, AGORA + timedelta(minutes=5))
    return o


# ------------------------------------------------------------------ chave

def test_gerar_chave_tem_tamanho_e_alfabeto_sem_caracteres_ambiguos():
    chaves = {gerar_chave_autenticidade() for _ in range(50)}
    assert len(chaves) == 50
    for chave in chaves:
        assert len(chave) == TAMANHO_CHAVE and all(c in ALFABETO_CHAVE for c in chave)
        assert not any(c in chave for c in "0O1I")


def test_formatar_chave_agrupa_de_quatro_em_quatro():
    assert formatar_chave(CHAVE) == "ABCD-ABCD-ABCD-ABCD-ABCD-ABCD"


@pytest.mark.parametrize("entrada", [CHAVE, CHAVE.lower(), "abcd-abcd abcd_abcd-ABCD-abcd", f"  {CHAVE}\n"])
def test_interpretar_codigo_aceita_chave_como_digitada(entrada):
    codigo = interpretar_codigo(entrada)
    assert codigo.tipo is TipoCodigoVerificacao.CHAVE and codigo.valor == CHAVE


@pytest.mark.parametrize("entrada", [HASH, HASH.upper(), f" {HASH[:32]}-{HASH[32:]} "])
def test_interpretar_codigo_reconhece_hash_sha256(entrada):
    codigo = interpretar_codigo(entrada)
    assert codigo.tipo is TipoCodigoVerificacao.HASH and codigo.valor == HASH


@pytest.mark.parametrize("entrada", [None, "", "ABC", CHAVE[:-1], "0OI1" * 6, HASH[:-2], "z" * 64])
def test_interpretar_codigo_rejeita_formato_invalido(entrada):
    with pytest.raises(ValorInvalidoError) as exc:
        interpretar_codigo(entrada)
    assert exc.value.chave == "documento.codigo_invalido"


# --------------------------------------------------------------- entidade

def test_registrada_nao_possui_documento_emitido():
    o = _registrada()
    assert o.chave_autenticidade is None and o.situacao_documento() is None and o.emitida_em() is None


def test_validar_emite_chave_e_documento_autentico():
    o = _validada()
    assert o.chave_autenticidade is not None and len(o.chave_autenticidade) == TAMANHO_CHAVE
    assert o.situacao_documento() is SituacaoDocumento.AUTENTICO
    assert o.emitida_em() == AGORA + timedelta(minutes=5)


def test_narrativa_adulterada_apos_emissao_e_detectada():
    o = _validada()
    o.descricao = "Narrativa alterada diretamente no banco após a validação."
    assert o.situacao_documento() is SituacaoDocumento.ADULTERADO


def test_documento_de_ocorrencia_excluida_fica_indisponivel():
    o = _validada()
    o.excluir(DELEGADO, "Registro anulado por decisão judicial.", AGORA + timedelta(hours=1))
    assert o.status is StatusOcorrencia.EXCLUIDA and o.situacao_documento() is SituacaoDocumento.INDISPONIVEL


def test_documento_arquivado_continua_autentico():
    o = _validada()
    o.arquivar(DELEGADO, "Sem novas diligências.", AGORA + timedelta(hours=1))
    assert o.situacao_documento() is SituacaoDocumento.AUTENTICO
