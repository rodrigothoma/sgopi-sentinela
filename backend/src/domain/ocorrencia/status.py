"""
Máquina de estados única da Ocorrência (DEC-02 — resolve DIV-03/04/05).

Estado inicial compulsório: AGUARDANDO_REVISAO (UC01 regra 3).
Estados terminais: REJEITADA, ENCERRADA.
"""
from enum import Enum


class StatusOcorrencia(str, Enum):
    AGUARDANDO_REVISAO = "AGUARDANDO_REVISAO"
    EM_CORRECAO = "EM_CORRECAO"
    REJEITADA = "REJEITADA"
    VALIDADA = "VALIDADA"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    ENCERRADA = "ENCERRADA"


# (estado_origem, operacao) -> estado_destino
TRANSICOES: dict[tuple[StatusOcorrencia, str], StatusOcorrencia] = {
    (StatusOcorrencia.AGUARDANDO_REVISAO, "validar"): StatusOcorrencia.VALIDADA,
    (StatusOcorrencia.AGUARDANDO_REVISAO, "devolver_para_correcao"): StatusOcorrencia.EM_CORRECAO,
    (StatusOcorrencia.AGUARDANDO_REVISAO, "rejeitar"): StatusOcorrencia.REJEITADA,
    (StatusOcorrencia.EM_CORRECAO, "reenviar"): StatusOcorrencia.AGUARDANDO_REVISAO,
    (StatusOcorrencia.VALIDADA, "despachar"): StatusOcorrencia.EM_ATENDIMENTO,
    (StatusOcorrencia.EM_ATENDIMENTO, "encerrar"): StatusOcorrencia.ENCERRADA,
}

ESTADOS_TERMINAIS = frozenset({StatusOcorrencia.REJEITADA, StatusOcorrencia.ENCERRADA})
ESTADOS_EDITAVEIS = frozenset({StatusOcorrencia.EM_CORRECAO})


def proximo_estado(atual: StatusOcorrencia, operacao: str) -> StatusOcorrencia | None:
    return TRANSICOES.get((atual, operacao))
