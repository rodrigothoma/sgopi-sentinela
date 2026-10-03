"""
Adapter de saída: Repositório de Notificações via SQLAlchemy async.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from infrastructure.database.models import NotificacaoModel


class NotificacaoRepositorioSQLAlchemy(RepositorioNotificacao):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def salvar(self, notificacao: Notificacao) -> Notificacao:
        stmt = select(NotificacaoModel).where(NotificacaoModel.id == notificacao.id)
        existente = (await self._session.execute(stmt)).scalar_one_or_none()

        tipo_str = notificacao.tipo.value if hasattr(notificacao.tipo, "value") else str(notificacao.tipo)
        prio_str = notificacao.prioridade.value if hasattr(notificacao.prioridade, "value") else str(notificacao.prioridade)

        if existente is None:
            model = NotificacaoModel(
                id=notificacao.id,
                usuario_id=notificacao.usuario_id,
                papel_destinatario=notificacao.papel_destinatario,
                departamento_destinatario=notificacao.departamento_destinatario,
                tipo=tipo_str,
                titulo=notificacao.titulo,
                mensagem=notificacao.mensagem,
                prioridade=prio_str,
                link=notificacao.link,
                lida=notificacao.lida,
                lida_em=notificacao.lida_em,
                metadados=notificacao.metadados,
                criada_em=notificacao.criada_em,
                ativo=notificacao.ativo,
            )
            self._session.add(model)
        else:
            existente.lida = notificacao.lida
            existente.lida_em = notificacao.lida_em
            existente.ativo = notificacao.ativo

        await self._session.flush()
        return notificacao

    async def obter_por_id(self, notificacao_id: UUID) -> Notificacao | None:
        stmt = select(NotificacaoModel).where(
            NotificacaoModel.id == notificacao_id,
            NotificacaoModel.ativo.is_(True),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def listar(
        self,
        usuario_id: UUID | None = None,
        papel: str | None = None,
        apenas_nao_lidas: bool = False,
        limite: int = 50,
    ) -> list[Notificacao]:
        condicoes = [NotificacaoModel.ativo.is_(True)]

        destinatarios = []
        if usuario_id is not None:
            destinatarios.append(NotificacaoModel.usuario_id == usuario_id)
        if papel is not None:
            destinatarios.append(NotificacaoModel.papel_destinatario == papel)
        # Notificações globais (sem destinatário específico)
        destinatarios.append((NotificacaoModel.usuario_id.is_(None)) & (NotificacaoModel.papel_destinatario.is_(None)))

        condicoes.append(or_(*destinatarios))

        if apenas_nao_lidas:
            condicoes.append(NotificacaoModel.lida.is_(False))

        stmt = (
            select(NotificacaoModel)
            .where(*condicoes)
            .order_by(NotificacaoModel.criada_em.desc())
            .limit(limite)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_domain(m) for m in models]

    async def contar_nao_lidas(self, usuario_id: UUID | None = None, papel: str | None = None) -> int:
        condicoes = [
            NotificacaoModel.ativo.is_(True),
            NotificacaoModel.lida.is_(False),
        ]

        destinatarios = []
        if usuario_id is not None:
            destinatarios.append(NotificacaoModel.usuario_id == usuario_id)
        if papel is not None:
            destinatarios.append(NotificacaoModel.papel_destinatario == papel)
        destinatarios.append((NotificacaoModel.usuario_id.is_(None)) & (NotificacaoModel.papel_destinatario.is_(None)))

        condicoes.append(or_(*destinatarios))

        stmt = select(func.count(NotificacaoModel.id)).where(*condicoes)
        return (await self._session.execute(stmt)).scalar_one()

    async def marcar_todas_lidas(self, usuario_id: UUID | None, papel: str | None, instante: datetime) -> int:
        condicoes = [
            NotificacaoModel.ativo.is_(True),
            NotificacaoModel.lida.is_(False),
        ]

        destinatarios = []
        if usuario_id is not None:
            destinatarios.append(NotificacaoModel.usuario_id == usuario_id)
        if papel is not None:
            destinatarios.append(NotificacaoModel.papel_destinatario == papel)
        destinatarios.append((NotificacaoModel.usuario_id.is_(None)) & (NotificacaoModel.papel_destinatario.is_(None)))

        condicoes.append(or_(*destinatarios))

        stmt = (
            update(NotificacaoModel)
            .where(*condicoes)
            .values(lida=True, lida_em=instante)
        )
        res = await self._session.execute(stmt)
        await self._session.flush()
        return res.rowcount

    @staticmethod
    def _to_domain(model: NotificacaoModel) -> Notificacao:
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
            lida=model.lida,
            lida_em=aware(model.lida_em) if model.lida_em else None,
            metadados=model.metadados,
            criada_em=aware(model.criada_em),
            ativo=model.ativo,
        )
