from datetime import datetime
from uuid import uuid4
import pytest

from domain.interagencias.entity import (
    ComunicacaoInteragencias,
    DepartamentoSeguranca,
    NivelSigilo,
    PrioridadeComunicacao,
    StatusEntrega,
)
from domain.shared.exceptions import CampoObrigatorioError


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
        )
