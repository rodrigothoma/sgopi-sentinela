"""Testes unitários puros do ComunicacaoInteragenciasMapper (sem banco de dados)."""
from datetime import UTC, datetime
from uuid import uuid4

from adapters.outbound.persistence.mappers import ComunicacaoInteragenciasMapper
from domain.interagencias.entity import (
    ComunicacaoInteragencias,
    NivelSigilo,
    PrioridadeComunicacao,
    StatusEntrega,
)
from infrastructure.database.models import ComunicacaoInteragenciasModel

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)
AGORA_NAIVE = AGORA.replace(tzinfo=None)


def _comunicacao() -> ComunicacaoInteragencias:
    return ComunicacaoInteragencias(
        numero_oficio="OFI-2026-000001",
        departamento_origem="POLICIA_CIVIL",
        departamentos_destinatarios=["POLICIA_MILITAR", "POLICIA_CIENTIFICA"],
        remetente_id=uuid4(),
        assunto="Solicitação de apoio",
        corpo="Solicito apoio tático para cumprimento de mandado.",
        criada_em=AGORA,
        protocolo_ocorrencia="BO-2026-000001",
        nivel_sigilo=NivelSigilo.RESERVADO,
        prioridade=PrioridadeComunicacao.ALTA,
        status_entrega=StatusEntrega.PENDENTE,
        mensagem_pai_id=uuid4(),
    )


def test_comunicacao_roundtrip() -> None:
    comunicacao = _comunicacao()

    model = ComunicacaoInteragenciasMapper.to_model(comunicacao)

    assert model.id == comunicacao.id
    assert model.numero_oficio == "OFI-2026-000001"
    assert model.nivel_sigilo == "RESERVADO"
    assert model.prioridade == "ALTA"
    assert model.status_entrega == "PENDENTE"
    assert model.departamentos_destinatarios == ["POLICIA_MILITAR", "POLICIA_CIENTIFICA"]
    assert model.departamentos_destinatarios is not comunicacao.departamentos_destinatarios

    assert ComunicacaoInteragenciasMapper.to_domain(model) == comunicacao


def test_atualizar_model_so_altera_entrega_e_ativo() -> None:
    """O ofício é um documento rastreável: assunto e corpo não são regravados."""
    comunicacao = _comunicacao()
    model = ComunicacaoInteragenciasMapper.to_model(comunicacao)
    comunicacao.status_entrega = StatusEntrega.ENTREGUE
    comunicacao.ativo = False
    comunicacao.corpo = "Corpo adulterado depois do envio."

    ComunicacaoInteragenciasMapper.atualizar_model(model, comunicacao)

    assert model.status_entrega == "ENTREGUE"
    assert model.ativo is False
    assert model.corpo == "Solicito apoio tático para cumprimento de mandado."


def test_to_domain_com_data_naive_e_enums_desconhecidos() -> None:
    model = ComunicacaoInteragenciasModel(
        id=uuid4(),
        numero_oficio="OFI-2026-000002",
        departamento_origem="POLICIA_CIVIL",
        departamentos_destinatarios=["DEFESA_CIVIL"],
        remetente_id=uuid4(),
        assunto="Ofício antigo",
        corpo="Registro gravado por uma versão anterior.",
        nivel_sigilo="SECRETO",
        prioridade="URGENTISSIMA",
        status_entrega="EXTRAVIADO",
        criada_em=AGORA_NAIVE,
        ativo=True,
    )

    comunicacao = ComunicacaoInteragenciasMapper.to_domain(model)

    assert comunicacao.criada_em == AGORA
    assert comunicacao.nivel_sigilo == NivelSigilo.PADRAO
    assert comunicacao.prioridade == PrioridadeComunicacao.MEDIA
    assert comunicacao.status_entrega == StatusEntrega.ENTREGUE
    assert comunicacao.protocolo_ocorrencia is None
    assert comunicacao.mensagem_pai_id is None
