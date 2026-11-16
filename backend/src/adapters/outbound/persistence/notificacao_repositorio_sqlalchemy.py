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

from adapters.outbound.persistence.mappers import NotificacaoMapper
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from domain.notificacao.entity import Notificacao
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
            self._session.add(NotificacaoMapper.to_model(notificacao))
        else:
            NotificacaoMapper.atualizar_model(existente, notificacao)
        await self._session.flush()
        return notificacao

    async def obter_por_id(self, notificacao_id: UUID) -> Notificacao | None:
        stmt = select(NotificacaoModel).where(NotificacaoModel.id == notificacao_id, NotificacaoModel.ativo.is_(True))
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return NotificacaoMapper.to_domain(model, None) if model else None

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
        return [NotificacaoMapper.to_domain(model, leitura) for model, leitura in linhas]

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

    async def buscar_por_metadado(self, chave: str, valor: str, tipo: str | None = None) -> Notificacao | None:
        # Caminho JSON do SQLAlchemy muda para json_extract no SQLite e ->> no PostgreSQL.
        stmt = (
            select(NotificacaoModel)
            .where(
                NotificacaoModel.ativo.is_(True),
                NotificacaoModel.metadados[chave].as_string() == valor,
            )
            .order_by(NotificacaoModel.criada_em.desc())
        )
        if tipo is not None:
            stmt = stmt.where(NotificacaoModel.tipo == tipo)
        model = (await self._session.execute(stmt)).scalars().first()
        return NotificacaoMapper.to_domain(model, None) if model else None
