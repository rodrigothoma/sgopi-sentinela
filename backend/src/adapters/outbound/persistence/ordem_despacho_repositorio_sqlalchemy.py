"""Adapter de saída: OrdemDespachoRepositorioSQLAlchemy + GeradorNumeroOrdemSQLAlchemy (RF18)."""
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.gerador_numero_ordem import GeradorNumeroOrdem, formatar_numero_ordem
from application.ports.outbound.repositorio_ordem_despacho import RepositorioOrdemDespacho
from domain.despacho.entity import OrdemDeDespacho
from infrastructure.database.models import OrdemDespachoModel

_UPSERT = text(
    "INSERT INTO sequencias_ordem_despacho (ano, ultimo) VALUES (:ano, 1) "
    "ON CONFLICT (ano) DO UPDATE SET ultimo = sequencias_ordem_despacho.ultimo + 1 RETURNING ultimo"
)


class GeradorNumeroOrdemSQLAlchemy(GeradorNumeroOrdem):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def proximo(self, ano: int) -> str:
        seq = (await self._session.execute(_UPSERT, {"ano": ano})).scalar_one()
        return formatar_numero_ordem(ano, int(seq))


class OrdemDespachoRepositorioSQLAlchemy(RepositorioOrdemDespacho):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def salvar(self, ordem: OrdemDeDespacho) -> None:
        model = await self._session.get(OrdemDespachoModel, ordem.id)
        if model is None:
            model = OrdemDespachoModel(id=ordem.id)
            self._session.add(model)
        model.numero, model.ocorrencia_id, model.viatura_id, model.operador_id = ordem.numero, ordem.ocorrencia_id, ordem.viatura_id, ordem.operador_id
        model.criada_em, model.observacoes, model.ativa, model.encerrada_em = ordem.criada_em, ordem.observacoes, ordem.ativa, ordem.encerrada_em
        await self._session.flush()

    async def buscar_por_id(self, ordem_id: UUID) -> OrdemDeDespacho | None:
        m = await self._session.get(OrdemDespachoModel, ordem_id)
        return self._to_domain(m) if m else None

    async def listar(self, ocorrencia_id: UUID | None = None, somente_ativas: bool = False, limit: int = 100) -> list[OrdemDeDespacho]:
        stmt = select(OrdemDespachoModel).order_by(OrdemDespachoModel.criada_em.desc()).limit(limit)
        if ocorrencia_id:
            stmt = stmt.where(OrdemDespachoModel.ocorrencia_id == ocorrencia_id)
        if somente_ativas:
            stmt = stmt.where(OrdemDespachoModel.ativa.is_(True))
        return [self._to_domain(m) for m in (await self._session.execute(stmt)).scalars().all()]

    @staticmethod
    def _to_domain(m: OrdemDespachoModel) -> OrdemDeDespacho:
        return OrdemDeDespacho(
            id=m.id, numero=m.numero, ocorrencia_id=m.ocorrencia_id, viatura_id=m.viatura_id, operador_id=m.operador_id,
            criada_em=aware(m.criada_em), observacoes=m.observacoes, ativa=m.ativa,
            encerrada_em=aware(m.encerrada_em) if m.encerrada_em else None,
        )
