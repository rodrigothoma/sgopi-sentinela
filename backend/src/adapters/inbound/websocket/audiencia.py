"""
Audiência dos eventos de tempo real (RF02 / RNF02 / LGPD).

O fan-out não é mais "todos recebem tudo": cada evento é entregue só a quem poderia lê-lo pela
API REST. Eventos operacionais (ocorrência, viatura, despacho) só carregam ids, status e
posições e seguem para qualquer sessão autenticada; os demais são filtrados por papel ou
destinatário. Um tipo desconhecido não é entregue a ninguém (falha fechada).
"""
from __future__ import annotations

from collections.abc import Callable

from application.ports.inbound.ator import Ator
from domain.shared.eventos import EventoDominio
from domain.usuario.entity import Papel

Regra = Callable[[EventoDominio, Ator], bool]

EVENTOS_OPERACIONAIS = frozenset(
    {
        "OcorrenciaValidada",
        "OcorrenciaDevolvida",
        "OcorrenciaRejeitada",
        "OcorrenciaReenviada",
        "OcorrenciaDespachada",
        "OcorrenciaEncerrada",
        "OcorrenciaArquivada",
        "OcorrenciaExcluida",
        "OcorrenciaPrioridadeAlterada",
        "OrdemDeDespachoCriada",
        "PosicaoAtualizada",
        "ViaturaSituacaoAlterada",
        "ViaturaChegouAoLocal",
    }
)
# Mesmos papéis das rotas REST correspondentes (medidas_router / interagencias_router)
PAPEIS_MEDIDAS = frozenset({Papel.DELEGADO, Papel.SUPERVISOR, Papel.OPERADOR_CENTRAL, Papel.AGENTE, Papel.ESCRIVAO})
PAPEIS_INTERAGENCIAS = frozenset({Papel.DELEGADO, Papel.SUPERVISOR, Papel.ESCRIVAO, Papel.OPERADOR_CENTRAL})


def _destinatario_da_notificacao(evento: EventoDominio, ator: Ator) -> bool:
    """Notificação pessoal só ao usuário; por papel só ao papel; sem alvo é global."""
    usuario_id = evento.dados.get("usuario_id")
    if usuario_id:
        return usuario_id == str(ator.id)
    papel = evento.dados.get("papel_destinatario")
    return not papel or papel == ator.papel.value


def _alerta_criticidade(evento: EventoDominio, ator: Ator) -> bool:
    papel = (evento.dados.get("dados") or {}).get("papel_destinatario")
    return not papel or papel == ator.papel.value


_REGRAS: dict[str, Regra] = {
    "NOTIFICACAO_EMITIDA": _destinatario_da_notificacao,
    "ALERTA_CRITICIDADE": _alerta_criticidade,
    "MEDIDA_VENCIMENTO_ALERTA": lambda _e, ator: ator.papel in PAPEIS_MEDIDAS,
    "COMUNICACAO_INTERAGENCIAS_CRIADA": lambda _e, ator: ator.papel in PAPEIS_INTERAGENCIAS,
}


def pode_receber(evento: EventoDominio, ator: Ator) -> bool:
    if evento.tipo in EVENTOS_OPERACIONAIS:
        return True
    regra = _REGRAS.get(evento.tipo)
    return regra is not None and regra(evento, ator)
