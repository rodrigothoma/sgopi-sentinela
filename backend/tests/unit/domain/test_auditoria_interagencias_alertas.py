"""Eventos de auditoria de ofícios interagências e alertas de criticidade (payloads iguais aos anteriores)."""
from datetime import UTC, datetime
from uuid import uuid4

from domain.auditoria.contexto import ContextoAuditoria
from domain.auditoria.evento import EventoAuditoria
from domain.interagencias.auditoria import OficioEnviado, OficioRespondido
from domain.interagencias.entity import ComunicacaoInteragencias
from domain.notificacao.auditoria import AlertaCriticidadeEmitido, CienciaAlertaRegistrada

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)
CONTEXTO = ContextoAuditoria(quem=uuid4(), quando=AGORA, ip="10.0.0.1")


def _oficio(**kw) -> ComunicacaoInteragencias:
    dados = dict(
        numero_oficio="OFI-2026-000001", departamento_origem="POLICIA_CIVIL", departamentos_destinatarios=["POLICIA_MILITAR"],
        remetente_id=uuid4(), assunto="Pedido de apoio tático", corpo="Solicita-se apoio de duas guarnições.", instante=AGORA,
        protocolo_ocorrencia="SGOPI-2026-000001",
    )
    dados.update(kw)
    return ComunicacaoInteragencias.criar(**dados)


def test_operacoes_entidades_e_grafias_legadas():
    assert {c.OPERACAO: c.ENTIDADE for c in (OficioEnviado, OficioRespondido, AlertaCriticidadeEmitido, CienciaAlertaRegistrada)} == {
        "interagencias.enviar": "comunicacoes_interagencias",
        "interagencias.responder": "comunicacoes_interagencias",
        "inteligencia.emitir_alerta": "inteligencia_criminal",
        "inteligencia.registrar_ciencia": "notificacoes",
    }
    assert EventoAuditoria.grafias("interagencias.enviar") == ("interagencias.enviar", "ENVIO_COMUNICACAO_INTERAGENCIAS")
    assert EventoAuditoria.grafias("interagencias.responder")[1] == "RESPOSTA_COMUNICACAO_INTERAGENCIAS"
    assert EventoAuditoria.grafias("inteligencia.emitir_alerta")[1] == "EMISSAO_ALERTA_CRITICIDADE"
    assert EventoAuditoria.grafias("inteligencia.registrar_ciencia")[1] == "CIENCIA_ALERTA_CRITICIDADE"


def test_oficio_enviado_e_respondido():
    oficio = _oficio()
    resposta = _oficio(numero_oficio="OFI-2026-000002", mensagem_pai_id=oficio.id)

    enviado = OficioEnviado.de(oficio).para_registro(CONTEXTO)
    respondido = OficioRespondido.de(resposta).para_registro(CONTEXTO)

    assert enviado.entidade_id == str(oficio.id)
    assert enviado.dados_depois == {
        "numero_oficio": "OFI-2026-000001", "origem": "POLICIA_CIVIL", "destinatarios": ["POLICIA_MILITAR"],
        "assunto": "Pedido de apoio tático", "protocolo": "SGOPI-2026-000001",
    }
    assert respondido.dados_depois == {"mensagem_pai_id": str(oficio.id), "numero_oficio": "OFI-2026-000002"}


def test_alerta_e_ciencia():
    alerta_id = uuid4()
    dados_alerta = {"titulo": "Área crítica", "nivel_criticidade": "CRITICA"}

    emitido = AlertaCriticidadeEmitido(notificacao_id=alerta_id, dados_alerta=dados_alerta).para_registro(CONTEXTO)
    ciencia = CienciaAlertaRegistrada(notificacao_id=alerta_id, supervisor="supervisor", papel="SUPERVISOR").para_registro(CONTEXTO)

    assert emitido.entidade_id == str(alerta_id) and emitido.dados_depois == dados_alerta
    assert ciencia.entidade_id == str(alerta_id) and ciencia.dados_depois == {"supervisor": "supervisor", "papel": "SUPERVISOR"}
