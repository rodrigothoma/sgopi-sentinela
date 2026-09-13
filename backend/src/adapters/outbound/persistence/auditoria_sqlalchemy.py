"""Adapter de saída: AuditoriaSQLAlchemy — append-only (RF20 / RNF03*)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.porta_auditoria import PortaAuditoria
from domain.auditoria.entity import RegistroAuditoria
from infrastructure.database.models import RegistroAuditoriaModel


class AuditoriaSQLAlchemy(PortaAuditoria):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar(self, registro: RegistroAuditoria) -> None:
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

    async def listar(self, entidade=None, entidade_id=None, limit=100) -> list[RegistroAuditoria]:
        stmt = select(RegistroAuditoriaModel).order_by(RegistroAuditoriaModel.quando.desc()).limit(limit)
        if entidade:
            stmt = stmt.where(RegistroAuditoriaModel.entidade == entidade)
        if entidade_id:
            stmt = stmt.where(RegistroAuditoriaModel.entidade_id == entidade_id)
        rows = (await self._session.execute(stmt)).scalars().all()
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
