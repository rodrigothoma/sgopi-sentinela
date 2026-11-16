"""Montagem das mensagens do registro; persistência e publicação pertencem ao caso de uso."""
from datetime import datetime

from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from domain.ocorrencia.entity import Ocorrencia
from domain.ocorrencia.eventos import ocorrencia_criada
from domain.shared.eventos import EventoDominio
from domain.usuario.entity import Papel

ROTA_FILA_DELEGADO = "/fila"
TITULO_NOVA_OCORRENCIA = "Nova ocorrência {protocolo} aguardando revisão"


def montar_evento_registro(ocorrencia: Ocorrencia, agora: datetime) -> EventoDominio:
    """Expõe o mesmo resumo operacional usado pela fila e pelos toasts."""
    return ocorrencia_criada(
        ocorrencia.id,
        agora,
        numero_protocolo=ocorrencia.numero_protocolo,
        natureza=ocorrencia.natureza,
        localizacao=ocorrencia.localizacao,
        latitude=ocorrencia.coordenada.latitude,
        longitude=ocorrencia.coordenada.longitude,
        prioridade=ocorrencia.prioridade.value,
        criada_em=ocorrencia.criada_em.isoformat(),
        agente_policial_id=str(ocorrencia.agente_policial_id),
        origem=ocorrencia.origem.value,
    )


def montar_notificacao_registro(ocorrencia: Ocorrencia, agora: datetime) -> Notificacao:
    """Prepara o aviso persistente do Delegado, sem realizar I/O ou confirmar a transação."""
    protocolo = ocorrencia.numero_protocolo
    return Notificacao.criar(
        titulo=TITULO_NOVA_OCORRENCIA.format(protocolo=protocolo),
        mensagem=f"{ocorrencia.natureza} — {ocorrencia.localizacao}",
        tipo=TipoNotificacao.NOVA_OCORRENCIA,
        prioridade=PrioridadeNotificacao.MEDIA,
        papel_destinatario=Papel.DELEGADO.value,
        link=f"{ROTA_FILA_DELEGADO}?ocorrencia={ocorrencia.id}",
        metadados={
            "ocorrencia_id": str(ocorrencia.id),
            "numero_protocolo": protocolo,
            "natureza": ocorrencia.natureza,
            "status": ocorrencia.status.value,
        },
        instante=agora,
    )
