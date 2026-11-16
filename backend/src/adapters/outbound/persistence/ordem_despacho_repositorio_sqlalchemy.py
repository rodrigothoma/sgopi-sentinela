"""Adapter de saída: OrdemDespachoRepositorioSQLAlchemy + GeradorNumeroOrdemSQLAlchemy (RF02)."""
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.mappers import OrdemDespachoMapper
from application.ports.outbound.gerador_numero_ordem import GeradorNumeroOrdem, formatar_numero_ordem
from application.ports.outbound.repositorio_ordem_despacho import RepositorioOrdemDespacho
from domain.despacho.entity import OrdemDeDespacho
from domain.shared.exceptions import ConflitoError
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
            self._session.add(OrdemDespachoMapper.to_model(ordem))
        else:
            OrdemDespachoMapper.atualizar_model(model, ordem)
        try:
            await self._session.flush()
        except IntegrityError as exc:  # uq_ordens_despacho_viatura_ativa: despacho concorrente da mesma viatura
            raise ConflitoError(
                "A viatura já está em outra ordem de despacho ativa.", chave="despacho.viatura_indisponivel"
            ) from exc

    async def buscar_por_id(self, ordem_id: UUID) -> OrdemDeDespacho | None:
        m = await self._session.get(OrdemDespachoModel, ordem_id)
        return OrdemDespachoMapper.to_domain(m) if m else None

    async def listar(self, ocorrencia_id: UUID | None = None, somente_ativas: bool = False, limit: int = 100) -> list[OrdemDeDespacho]:
        stmt = select(OrdemDespachoModel).order_by(OrdemDespachoModel.criada_em.desc()).limit(limit)
        if ocorrencia_id:
            stmt = stmt.where(OrdemDespachoModel.ocorrencia_id == ocorrencia_id)
        if somente_ativas:
            stmt = stmt.where(OrdemDespachoModel.ativa.is_(True))
        return [OrdemDespachoMapper.to_domain(m) for m in (await self._session.execute(stmt)).scalars().all()]

    async def buscar_ativa_por_viatura(self, viatura_id: UUID) -> OrdemDeDespacho | None:
        stmt = (
            select(OrdemDespachoModel)
            .where(OrdemDespachoModel.viatura_id == viatura_id, OrdemDespachoModel.ativa.is_(True))
            .order_by(OrdemDespachoModel.criada_em.desc())
            .limit(1)
        )
        m = (await self._session.execute(stmt)).scalar_one_or_none()
        return OrdemDespachoMapper.to_domain(m) if m else None
