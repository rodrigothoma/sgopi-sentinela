"""
Máquina de estados única da Ocorrência (DEC-02 — resolve DIV-03/04/05).

Estado inicial compulsório: AGUARDANDO_REVISAO (UC01 regra 3).
Estados terminais do fluxo operacional: REJEITADA, ENCERRADA.

Atos administrativos privativos do Delegado (RF20 — exigem motivo):
- ``arquivar``: retira a ocorrência do fluxo sem apagá-la (ARQUIVADA);
- ``excluir``: exclusão *lógica* (EXCLUIDA) — nada é apagado do banco (RNF03*),
  a ocorrência apenas some das listagens sem filtro explícito.
Nenhum dos dois é permitido em EM_ATENDIMENTO (há viatura empenhada).
"""
from enum import Enum


class StatusOcorrencia(str, Enum):
    AGUARDANDO_REVISAO = "AGUARDANDO_REVISAO"
    EM_CORRECAO = "EM_CORRECAO"
    REJEITADA = "REJEITADA"
    VALIDADA = "VALIDADA"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    ENCERRADA = "ENCERRADA"
    ARQUIVADA = "ARQUIVADA"
    EXCLUIDA = "EXCLUIDA"


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

# RF03 / UC03 pré-condição: "ocorrência registrada ou em andamento" aceita novos itens apreendidos.
ESTADOS_ACEITAM_APREENSAO = frozenset(
    {
        StatusOcorrencia.AGUARDANDO_REVISAO,
        StatusOcorrencia.EM_CORRECAO,
        StatusOcorrencia.VALIDADA,
        StatusOcorrencia.EM_ATENDIMENTO,
    }
)

# Arquivar: qualquer estado fora do atendimento e que ainda não foi arquivado/excluído.
ESTADOS_ARQUIVAVEIS = frozenset(
    {
        StatusOcorrencia.AGUARDANDO_REVISAO,
        StatusOcorrencia.EM_CORRECAO,
        StatusOcorrencia.REJEITADA,
        StatusOcorrencia.VALIDADA,
        StatusOcorrencia.ENCERRADA,
    }
)
# Excluir: os mesmos + ARQUIVADA. EXCLUIDA é terminal absoluto.
ESTADOS_EXCLUIVEIS = ESTADOS_ARQUIVAVEIS | {StatusOcorrencia.ARQUIVADA}

TRANSICOES.update({(origem, "arquivar"): StatusOcorrencia.ARQUIVADA for origem in ESTADOS_ARQUIVAVEIS})
TRANSICOES.update({(origem, "excluir"): StatusOcorrencia.EXCLUIDA for origem in ESTADOS_EXCLUIVEIS})

# Listagens sem filtro explícito não mostram excluídas (mas o detalhe segue consultável).
ESTADOS_VISIVEIS_POR_PADRAO = tuple(s for s in StatusOcorrencia if s is not StatusOcorrencia.EXCLUIDA)


def proximo_estado(atual: StatusOcorrencia, operacao: str) -> StatusOcorrencia | None:
    return TRANSICOES.get((atual, operacao))
