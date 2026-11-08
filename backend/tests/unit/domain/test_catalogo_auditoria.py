"""Catálogo da trilha de auditoria (RNF03)."""
from datetime import UTC, datetime
from uuid import uuid4

from domain.auditoria.catalogo import EntidadeAuditada, OperacaoAuditada, grafias
from domain.auditoria.entity import RegistroAuditoria

AGORA = datetime(2026, 11, 9, tzinfo=UTC)


def test_operacoes_seguem_formato_dominio_acao():
    assert all(o.value.count(".") == 1 and o.value == o.value.lower() for o in OperacaoAuditada)


def test_registro_guarda_texto_puro_e_nao_o_membro_do_enum():
    registro = RegistroAuditoria(
        quem=uuid4(), quando=AGORA, operacao=OperacaoAuditada.OCORRENCIA_VALIDAR, entidade=EntidadeAuditada.OCORRENCIA, entidade_id="1"
    )

    assert type(registro.operacao) is str and registro.operacao == "ocorrencia.validar"
    assert type(registro.entidade) is str and registro.entidade == "Ocorrencia"


def test_grafias_incluem_as_legadas_depois_da_canonica():
    assert grafias(OperacaoAuditada.INTERAGENCIAS_ENVIAR) == ("interagencias.enviar", "ENVIO_COMUNICACAO_INTERAGENCIAS")
    assert grafias(EntidadeAuditada.MEDIDA_PROTETIVA) == ("medida_protetiva", "medidas_protetivas")
    assert grafias(OperacaoAuditada.AUTH_LOGIN) == ("auth.login",)
