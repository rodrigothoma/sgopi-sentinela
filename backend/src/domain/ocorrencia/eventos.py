"""Eventos de domínio do contexto de ocorrências (consumidos por tempo real / RF02 e RNF01)."""
from datetime import datetime
from uuid import UUID

from domain.shared.eventos import EventoDominio


def _evento(tipo: str, ocorrencia_id: UUID, status: str, em: datetime, **extra: object) -> EventoDominio:
    return EventoDominio(
        tipo=tipo,
        ocorrido_em=em,
        dados={"ocorrencia_id": str(ocorrencia_id), "status": status, **extra},
    )


def ocorrencia_validada(ocorrencia_id: UUID, em: datetime, **extra: object) -> EventoDominio:
    return _evento("OcorrenciaValidada", ocorrencia_id, "VALIDADA", em, **extra)


def ocorrencia_devolvida(ocorrencia_id: UUID, em: datetime, **extra: object) -> EventoDominio:
    return _evento("OcorrenciaDevolvida", ocorrencia_id, "EM_CORRECAO", em, **extra)


def ocorrencia_rejeitada(ocorrencia_id: UUID, em: datetime, **extra: object) -> EventoDominio:
    return _evento("OcorrenciaRejeitada", ocorrencia_id, "REJEITADA", em, **extra)


def ocorrencia_reenviada(ocorrencia_id: UUID, em: datetime, **extra: object) -> EventoDominio:
    return _evento("OcorrenciaReenviada", ocorrencia_id, "AGUARDANDO_REVISAO", em, **extra)


def ocorrencia_despachada(ocorrencia_id: UUID, em: datetime, **extra: object) -> EventoDominio:
    return _evento("OcorrenciaDespachada", ocorrencia_id, "EM_ATENDIMENTO", em, **extra)


def ocorrencia_encerrada(ocorrencia_id: UUID, em: datetime, **extra: object) -> EventoDominio:
    return _evento("OcorrenciaEncerrada", ocorrencia_id, "ENCERRADA", em, **extra)
