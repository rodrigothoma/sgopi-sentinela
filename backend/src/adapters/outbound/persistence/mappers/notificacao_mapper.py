"""
Data Mapper para a entidade Notificacao (HEX-03 / SRP).

Isola a lógica de conversão bidirecional entre Notificacao (Domain) e NotificacaoModel (SQLAlchemy).
"""
from __future__ import annotations

from datetime import datetime

from adapters.outbound.persistence._datas import aware, aware_opcional
from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from domain.shared.enums import interpretar_enum_ou_padrao
from infrastructure.database.models import NotificacaoModel


class NotificacaoMapper:
    """Mapeamento entre a entidade Notificacao e o modelo relacional NotificacaoModel.

    O estado de leitura é individual e vive em ``notificacoes_leituras``: as colunas ``lida``/``lida_em``
    da notificação nunca são gravadas, e a leitura do usuário consultado chega ao ``to_domain`` por fora.
    """

    @staticmethod
    def atualizar_model(model: NotificacaoModel, notificacao: Notificacao) -> None:
        """Só a retirada lógica é regravada; o conteúdo de uma notificação emitida não muda."""
        model.ativo = notificacao.ativo

    @staticmethod
    def to_model(notificacao: Notificacao) -> NotificacaoModel:
        return NotificacaoModel(
            id=notificacao.id,
            usuario_id=notificacao.usuario_id,
            papel_destinatario=notificacao.papel_destinatario,
            departamento_destinatario=notificacao.departamento_destinatario,
            tipo=notificacao.tipo.value,
            titulo=notificacao.titulo,
            mensagem=notificacao.mensagem,
            prioridade=notificacao.prioridade.value,
            link=notificacao.link,
            lida=False,
            lida_em=None,
            metadados=notificacao.metadados,
            criada_em=notificacao.criada_em,
            ativo=notificacao.ativo,
        )

    @staticmethod
    def to_domain(model: NotificacaoModel, lida_em: datetime | None) -> Notificacao:
        """``lida_em`` é o instante em que o usuário consultado leu a notificação (``None`` = pendente para ele).

        Tipo ou prioridade que não existem mais no enum caem no padrão, para um registro antigo não quebrar a listagem.
        """
        return Notificacao(
            id=model.id,
            titulo=model.titulo,
            mensagem=model.mensagem,
            tipo=interpretar_enum_ou_padrao(TipoNotificacao, model.tipo, TipoNotificacao.SISTEMA),
            prioridade=interpretar_enum_ou_padrao(PrioridadeNotificacao, model.prioridade, PrioridadeNotificacao.MEDIA),
            usuario_id=model.usuario_id,
            papel_destinatario=model.papel_destinatario,
            departamento_destinatario=model.departamento_destinatario,
            link=model.link,
            lida=lida_em is not None,
            lida_em=aware_opcional(lida_em),
            metadados=model.metadados,
            criada_em=aware(model.criada_em),
            ativo=model.ativo,
        )
