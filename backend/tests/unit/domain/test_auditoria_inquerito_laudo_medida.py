"""Eventos de auditoria de inquérito, laudo e medida protetiva (payloads iguais aos anteriores)."""
from datetime import UTC, date, datetime
from uuid import uuid4

from domain.auditoria.contexto import ContextoAuditoria
from domain.auditoria.evento import EventoAuditoria
from domain.inquerito.auditoria import InqueritoConcluido, InqueritoInstaurado, OcorrenciasVinculadasAoInquerito
from domain.inquerito.entity import Inquerito
from domain.laudo.auditoria import LaudoAnexado, LaudoBaixado, LaudoSolicitado
from domain.laudo.entity import LaudoPericial, TipoPericia
from domain.medida_protetiva.auditoria import AlertaVencimentoEmitido, MedidaConcedida, MedidaRenovada, MedidaRevogada
from domain.medida_protetiva.entity import MedidaProtetiva

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)
CONTEXTO = ContextoAuditoria(quem=uuid4(), quando=AGORA, ip="10.0.0.1")
HASH = "a" * 64


def test_operacoes_e_entidades():
    assert {c.OPERACAO: c.ENTIDADE for c in (InqueritoInstaurado, OcorrenciasVinculadasAoInquerito, InqueritoConcluido)} == {
        "inquerito.instaurar": "inquerito",
        "inquerito.vincular_ocorrencias": "inquerito",
        "inquerito.concluir": "inquerito",
    }
    assert {c.OPERACAO: c.ENTIDADE for c in (LaudoSolicitado, LaudoAnexado, LaudoBaixado)} == {
        "laudo.solicitar": "laudo_pericial",
        "laudo.anexar": "laudo_pericial",
        "laudo.download": "laudo_pericial",
    }
    assert {c.OPERACAO: c.ENTIDADE for c in (MedidaConcedida, MedidaRenovada, MedidaRevogada, AlertaVencimentoEmitido)} == {
        "medida_protetiva.conceder": "medida_protetiva",
        "medida_protetiva.renovar": "medida_protetiva",
        "medida_protetiva.revogar": "medida_protetiva",
        "medida_protetiva.alertar_vencimento": "medida_protetiva",
    }
    assert "medidas_protetivas" in EventoAuditoria.grafias_da_entidade("medida_protetiva")
    assert "ALERTA_VENCIMENTO_MEDIDA" in EventoAuditoria.grafias("medida_protetiva.alertar_vencimento")


def _inquerito(ocorrencias=()) -> Inquerito:
    return Inquerito.instaurar(
        numero="IP-2026-000001", ementa="Furtos em série no centro.", delegado_id=uuid4(), instante=AGORA,
        ocorrencias_iniciais_ids=list(ocorrencias),
    )


def test_eventos_de_inquerito_comecam_pelo_numero():
    oc1, oc2 = uuid4(), uuid4()
    inquerito = _inquerito([oc1])

    instaurado = InqueritoInstaurado.de(inquerito).para_registro(CONTEXTO)
    inquerito.vincular_ocorrencia(oc2, AGORA)
    vinculo = OcorrenciasVinculadasAoInquerito.de(inquerito, novas=[oc2]).para_registro(CONTEXTO)
    inquerito.concluir("Relatório final com autoria e materialidade.", AGORA)
    concluido = InqueritoConcluido.de(inquerito).para_registro(CONTEXTO)

    assert instaurado.entidade_id == str(inquerito.id)
    assert instaurado.dados_depois == {"numero": "IP-2026-000001", "ementa": "Furtos em série no centro.", "ocorrencias_vinculadas": [str(oc1)]}
    assert vinculo.dados_depois == {"numero": "IP-2026-000001", "novas_vinculadas": [str(oc2)], "total_vinculadas": 2}
    assert concluido.dados_depois == {"numero": "IP-2026-000001", "status": "CONCLUIDO"}


def test_eventos_de_laudo():
    ocorrencia_id = uuid4()
    laudo = LaudoPericial.solicitar(
        numero_referencia="LP-2026-000001", tipo_pericia=TipoPericia.BALISTICA, descricao_solicitacao="Exame de projéteis recolhidos.",
        solicitante_id=uuid4(), instante=AGORA, ocorrencia_id=ocorrencia_id,
    )

    solicitado = LaudoSolicitado.de(laudo).para_registro(CONTEXTO)
    laudo.anexar_laudo_concluido(
        perito_id=uuid4(), conclusoes_tecnicas="Projéteis compatíveis com a arma apreendida.", arquivo_chave="k",
        arquivo_nome="laudo.pdf", hash_sha256=HASH, instante=AGORA,
    )
    anexado = LaudoAnexado.de(laudo).para_registro(CONTEXTO)
    baixado = LaudoBaixado.de(laudo, integridade="INTEGRO").para_registro(CONTEXTO)

    assert solicitado.dados_depois == {
        "numero_referencia": "LP-2026-000001", "tipo_pericia": "BALISTICA", "ocorrencia_id": str(ocorrencia_id), "inquerito_id": None,
    }
    assert anexado.dados_depois == {"numero_referencia": "LP-2026-000001", "arquivo_nome": "laudo.pdf", "hash_sha256": HASH, "status": laudo.status.value}
    assert baixado.dados_depois == {"numero_referencia": "LP-2026-000001", "integridade": "INTEGRO"}


def _medida() -> MedidaProtetiva:
    return MedidaProtetiva.conceder(
        numero_referencia="MP-2026-000001", ocorrencia_id=uuid4(), delegado_id=uuid4(), vitima_id=uuid4(), agressor_id=uuid4(),
        tipos_restricao=["AFASTAMENTO_DO_LAR"], data_inicio=date(2026, 11, 16), prazo_dias=30, instante=AGORA,
    )


def test_eventos_de_medida():
    medida = _medida()

    concedida = MedidaConcedida.de(medida).para_registro(CONTEXTO)
    vencimento_anterior = medida.data_vencimento
    medida.renovar(dias_adicionais=10, justificativa="Persistência das ameaças relatadas.", instante=AGORA)
    renovada = MedidaRenovada.de(medida, vencimento_anterior, 10, "Persistência das ameaças relatadas.").para_registro(CONTEXTO)
    medida.revogar(motivo="Decisão judicial superveniente.", instante=AGORA)
    revogada = MedidaRevogada.de(medida, status_anterior="RENOVADA", motivo="Decisão judicial superveniente.").para_registro(CONTEXTO)

    assert concedida.dados_depois == {
        "numero_referencia": "MP-2026-000001", "ocorrencia_id": str(medida.ocorrencia_id), "vitima_id": str(medida.vitima_id),
        "agressor_id": str(medida.agressor_id), "tipos_restricao": ["AFASTAMENTO_DO_LAR"], "prazo_dias": 30,
        "data_vencimento": "2026-12-16",
    }
    assert renovada.dados_antes == {"data_vencimento": "2026-12-16", "prazo_dias": 30}
    assert renovada.dados_depois == {
        "data_vencimento": "2026-12-26", "prazo_dias": 40, "dias_adicionais": 10, "justificativa": "Persistência das ameaças relatadas.",
    }
    assert revogada.dados_antes == {"status": "RENOVADA"}
    assert revogada.dados_depois == {"status": "REVOGADA", "motivo_revogacao": "Decisão judicial superveniente."}


def test_alerta_de_vencimento():
    medida = _medida()

    registro = AlertaVencimentoEmitido.de(
        medida, dias_restantes=2, email_destinatario="vitima@exemplo.com", email_enviado=True, manual=False
    ).para_registro(CONTEXTO)

    assert registro.dados_depois == {
        "numero_referencia": "MP-2026-000001", "dias_restantes": 2, "email_destinatario": "vitima@exemplo.com",
        "email_enviado": True, "manual": False,
    }
