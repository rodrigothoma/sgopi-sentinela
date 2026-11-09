from datetime import UTC, datetime
from uuid import uuid4

import pytest

from domain.interagencias.entity import (
    ComunicacaoInteragencias,
    NivelSigilo,
    PrioridadeComunicacao,
    StatusEntrega,
)
from domain.shared.exceptions import CampoObrigatorioError, ValorInvalidoError


def test_criar_comunicacao_interagencias_valida():
    remetente_id = uuid4()
    com = ComunicacaoInteragencias.criar(
        numero_oficio="OFI-2026-000001",
        departamento_origem="POLICIA_CIVIL",
        departamentos_destinatarios=["POLICIA_MILITAR", "POLICIA_CIENTIFICA"],
        remetente_id=remetente_id,
        assunto="Solicitação de Apoio Pericial em Furto Qualificado",
        corpo="Solicita-se envio de equipe de papiloscopia para levantamento de vestígios.",
        protocolo_ocorrencia="2026-000123",
        nivel_sigilo=NivelSigilo.RESERVADO,
        prioridade=PrioridadeComunicacao.ALTA,
        instante=datetime.now(UTC),
    )
    assert com.numero_oficio == "OFI-2026-000001"
    assert com.departamento_origem == "POLICIA_CIVIL"
    assert "POLICIA_MILITAR" in com.departamentos_destinatarios
    assert "POLICIA_CIENTIFICA" in com.departamentos_destinatarios
    assert com.nivel_sigilo == NivelSigilo.RESERVADO
    assert com.prioridade == PrioridadeComunicacao.ALTA
    assert com.status_entrega == StatusEntrega.ENTREGUE
    assert com.ativo is True


def test_validacao_assunto_curto():
    with pytest.raises(CampoObrigatorioError, match="assunto"):
        ComunicacaoInteragencias.criar(
            numero_oficio="OFI-1",
            departamento_origem="POLICIA_CIVIL",
            departamentos_destinatarios=["POLICIA_MILITAR"],
            remetente_id=uuid4(),
            assunto="Aj",
            corpo="Corpo com mais de dez caracteres",
            instante=datetime.now(UTC),
        )


def test_validacao_destinatarios_vazio():
    with pytest.raises(CampoObrigatorioError, match="departamento destinatário"):
        ComunicacaoInteragencias.criar(
            numero_oficio="OFI-1",
            departamento_origem="POLICIA_CIVIL",
            departamentos_destinatarios=[],
            remetente_id=uuid4(),
            assunto="Assunto válido",
            corpo="Corpo com mais de dez caracteres",
            instante=datetime.now(UTC),
        )


def _criar(**kw):
    dados = dict(
        numero_oficio="OFI-1",
        departamento_origem="POLICIA_CIVIL",
        departamentos_destinatarios=["policia_militar", "  "],
        remetente_id=uuid4(),
        assunto="Assunto válido",
        corpo="Corpo com mais de dez caracteres",
        instante=datetime.now(UTC),
    )
    dados.update(kw)
    return ComunicacaoInteragencias.criar(**dados)


@pytest.mark.parametrize(
    "invalido",
    [{"numero_oficio": " "}, {"departamento_origem": ""}, {"corpo": "curto"}, {"departamentos_destinatarios": ["  "]}],
)
def test_campos_obrigatorios(invalido):
    with pytest.raises(CampoObrigatorioError):
        _criar(**invalido)


def test_normaliza_destinatarios_caixa_e_espacos():
    com = _criar(nivel_sigilo=" reservado ", prioridade="alta")
    assert com.departamentos_destinatarios == ["POLICIA_MILITAR"]
    assert com.nivel_sigilo == NivelSigilo.RESERVADO and com.prioridade == PrioridadeComunicacao.ALTA


def test_sigilo_desconhecido_e_recusado_em_vez_de_virar_padrao():
    """Regressão: valor inválido virava PADRAO e tornava público um ofício que se quis restrito."""
    with pytest.raises(ValorInvalidoError) as erro:
        _criar(nivel_sigilo="secreto")
    assert erro.value.chave == "interagencias.sigilo_invalido"


def test_prioridade_desconhecida_e_recusada():
    with pytest.raises(ValorInvalidoError) as erro:
        _criar(prioridade="urgentissima")
    assert erro.value.chave == "interagencias.prioridade_invalida"
