"""
Adapter de saída: Repositório de Notificações via SQLAlchemy async.

O estado de leitura vive em ``notificacoes_leituras`` (uma linha por usuário que leu): uma
notificação de papel ou de difusão lida por um usuário continua pendente para os demais.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import ColumnElement, and_, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from infrastructure.database.models import NotificacaoLeituraModel, NotificacaoModel


def _visivel_para(usuario_id: UUID | None, papel: str | None) -> ColumnElement[bool]:
    destinatarios = [and_(NotificacaoModel.usuario_id.is_(None), NotificacaoModel.papel_destinatario.is_(None))]
    if usuario_id is not None:
        destinatarios.append(NotificacaoModel.usuario_id == usuario_id)
    if papel is not None:
        destinatarios.append(and_(NotificacaoModel.usuario_id.is_(None), NotificacaoModel.papel_destinatario == papel))
    return and_(NotificacaoModel.ativo.is_(True), or_(*destinatarios))


def _lida_por(usuario_id: UUID | None) -> ColumnElement[bool]:
    return exists().where(
        NotificacaoLeituraModel.notificacao_id == NotificacaoModel.id,
        NotificacaoLeituraModel.usuario_id == usuario_id,
    )


class NotificacaoRepositorioSQLAlchemy(RepositorioNotificacao):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def salvar(self, notificacao: Notificacao) -> Notificacao:
        existente = await self._session.get(NotificacaoModel, notificacao.id)
        if existente is None:
            self._session.add(
                NotificacaoModel(
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
            )
        else:
            existente.ativo = notificacao.ativo
        await self._session.flush()
        return notificacao

    async def obter_por_id(self, notificacao_id: UUID) -> Notificacao | None:
        stmt = select(NotificacaoModel).where(NotificacaoModel.id == notificacao_id, NotificacaoModel.ativo.is_(True))
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model, None) if model else None

    async def listar(
        self,
        usuario_id: UUID | None = None,
        papel: str | None = None,
        apenas_nao_lidas: bool = False,
        limite: int = 50,
        offset: int = 0,
    ) -> list[Notificacao]:
        lida_em = (
            select(NotificacaoLeituraModel.lida_em)
            .where(
                NotificacaoLeituraModel.notificacao_id == NotificacaoModel.id,
                NotificacaoLeituraModel.usuario_id == usuario_id,
            )
            .scalar_subquery()
        )
        stmt = select(NotificacaoModel, lida_em).where(_visivel_para(usuario_id, papel))
        if apenas_nao_lidas:
            stmt = stmt.where(~_lida_por(usuario_id))
        stmt = stmt.order_by(NotificacaoModel.criada_em.desc()).limit(limite).offset(offset)
        linhas = (await self._session.execute(stmt)).all()
        return [self._to_domain(model, leitura) for model, leitura in linhas]

    async def contar_nao_lidas(self, usuario_id: UUID | None = None, papel: str | None = None) -> int:
        stmt = select(func.count(NotificacaoModel.id)).where(_visivel_para(usuario_id, papel), ~_lida_por(usuario_id))
        return int((await self._session.execute(stmt)).scalar_one())

    async def registrar_leitura(self, notificacao_id: UUID, usuario_id: UUID, instante: datetime) -> None:
        if await self._session.get(NotificacaoLeituraModel, (notificacao_id, usuario_id)) is None:
            self._session.add(NotificacaoLeituraModel(notificacao_id=notificacao_id, usuario_id=usuario_id, lida_em=instante))
            await self._session.flush()

    async def marcar_todas_lidas(self, usuario_id: UUID | None, papel: str | None, instante: datetime) -> int:
        if usuario_id is None:
            return 0
        stmt = select(NotificacaoModel.id).where(_visivel_para(usuario_id, papel), ~_lida_por(usuario_id))
        pendentes = (await self._session.execute(stmt)).scalars().all()
        self._session.add_all(
            NotificacaoLeituraModel(notificacao_id=nid, usuario_id=usuario_id, lida_em=instante) for nid in pendentes
        )
        await self._session.flush()
        return len(pendentes)

    @staticmethod
    def _to_domain(model: NotificacaoModel, lida_em: datetime | None) -> Notificacao:
        return Notificacao(
            id=model.id,
            titulo=model.titulo,
            mensagem=model.mensagem,
            tipo=TipoNotificacao(model.tipo) if model.tipo in TipoNotificacao.__members__ else TipoNotificacao.SISTEMA,
            prioridade=PrioridadeNotificacao(model.prioridade) if model.prioridade in PrioridadeNotificacao.__members__ else PrioridadeNotificacao.MEDIA,
            usuario_id=model.usuario_id,
            papel_destinatario=model.papel_destinatario,
            departamento_destinatario=model.departamento_destinatario,
            link=model.link,
            lida=lida_em is not None,
            lida_em=aware(lida_em) if lida_em else None,
            metadados=model.metadados,
            criada_em=aware(model.criada_em),
            ativo=model.ativo,
        )
