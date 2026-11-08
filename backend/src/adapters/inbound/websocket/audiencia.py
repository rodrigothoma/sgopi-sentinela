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
from domain.interagencias.entity import NivelSigilo, niveis_sigilo_visiveis
from domain.shared.eventos import EventoDominio
from domain.usuario.permissoes import Permissao

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


def _destinatario_da_notificacao(evento: EventoDominio, ator: Ator) -> bool:
    """Notificação pessoal só ao usuário; por papel só ao papel; sem alvo é global."""
    usuario_id = evento.dados.get("usuario_id")
    if usuario_id:
        return usuario_id == str(ator.id)
    papel = evento.dados.get("papel_destinatario")
    return not papel or papel == ator.papel.value


def _comunicacao_interagencias(evento: EventoDominio, ator: Ator) -> bool:
    """Papéis de interagências, filtrados pelo nível de sigilo do ofício (o remetente sempre recebe)."""
    if not ator.pode(Permissao.ENVIAR_OFICIO):
        return False
    if evento.dados.get("remetente_id") == str(ator.id):
        return True
    nivel = evento.dados.get("nivel_sigilo", NivelSigilo.PADRAO.value)
    return nivel in {n.value for n in niveis_sigilo_visiveis(ator.papel)}


def _alerta_criticidade(evento: EventoDominio, ator: Ator) -> bool:
    papel = (evento.dados.get("dados") or {}).get("papel_destinatario")
    return not papel or papel == ator.papel.value


_REGRAS: dict[str, Regra] = {
    "NOTIFICACAO_EMITIDA": _destinatario_da_notificacao,
    "ALERTA_CRITICIDADE": _alerta_criticidade,
    "MEDIDA_VENCIMENTO_ALERTA": lambda _e, ator: ator.pode(Permissao.CONSULTAR_MEDIDAS),
    "COMUNICACAO_INTERAGENCIAS_CRIADA": _comunicacao_interagencias,
}


def pode_receber(evento: EventoDominio, ator: Ator) -> bool:
    if evento.tipo in EVENTOS_OPERACIONAIS:
        return True
    regra = _REGRAS.get(evento.tipo)
    return regra is not None and regra(evento, ator)
