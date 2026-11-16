"""Adapter de saída: AuditoriaSQLAlchemy — append-only (RNF03*)."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.porta_auditoria import PortaAuditoria
from domain.auditoria.contexto import ContextoAuditoria
from domain.auditoria.entity import RegistroAuditoria
from domain.auditoria.evento import EventoAuditoria
from infrastructure.database.models import RegistroAuditoriaModel


class AuditoriaSQLAlchemy(PortaAuditoria):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar(self, evento: EventoAuditoria, contexto: ContextoAuditoria) -> None:
        registro = evento.para_registro(contexto)
        self._session.add(
            RegistroAuditoriaModel(
                id=registro.id,
                quem=registro.quem,
                quando=registro.quando,
                operacao=registro.operacao,
                entidade=registro.entidade,
                entidade_id=registro.entidade_id,
                dados_antes=registro.dados_antes,
                dados_depois=registro.dados_depois,
                ip=registro.ip,
            )
        )
        await self._session.flush()

    async def listar(
        self,
        entidade: str | None = None,
        entidade_id: str | None = None,
        operacao: str | None = None,
        quem: UUID | None = None,
        limit: int = 100,
        de: datetime | None = None,
        ate: datetime | None = None,
        offset: int = 0,
    ) -> list[RegistroAuditoria]:
        filtros = _filtros(entidade, entidade_id, operacao, quem, de, ate)
        stmt = select(RegistroAuditoriaModel).where(*filtros).order_by(RegistroAuditoriaModel.quando.desc())
        rows = (await self._session.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return [
            RegistroAuditoria(
                id=r.id,
                quem=r.quem,
                quando=aware(r.quando),
                operacao=r.operacao,
                entidade=r.entidade,
                entidade_id=r.entidade_id,
                dados_antes=r.dados_antes,
                dados_depois=r.dados_depois,
                ip=r.ip,
            )
            for r in rows
        ]

    async def contar(
        self,
        entidade: str | None = None,
        entidade_id: str | None = None,
        operacao: str | None = None,
        quem: UUID | None = None,
        de: datetime | None = None,
        ate: datetime | None = None,
    ) -> int:
        filtros = _filtros(entidade, entidade_id, operacao, quem, de, ate)
        stmt = select(func.count()).select_from(RegistroAuditoriaModel).where(*filtros)
        return int((await self._session.execute(stmt)).scalar_one())


def _filtros(
    entidade: str | None,
    entidade_id: str | None,
    operacao: str | None,
    quem: UUID | None,
    de: datetime | None,
    ate: datetime | None,
) -> list[ColumnElement[bool]]:
    """Condições comuns a ``listar`` e ``contar``: a página e o total sempre batem."""
    m = RegistroAuditoriaModel
    condicoes: list[ColumnElement[bool]] = []
    if entidade:
        condicoes.append(m.entidade == entidade)
    if entidade_id:
        condicoes.append(m.entidade_id == entidade_id)
    if operacao:
        condicoes.append(m.operacao == operacao)
    if quem:
        condicoes.append(m.quem == quem)
    if de is not None:
        condicoes.append(m.quando >= de)
    if ate is not None:
        condicoes.append(m.quando < ate)
    return condicoes
