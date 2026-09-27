"""
Adapter de saída: InqueritoRepositorioSQLAlchemy (RF06 / UC06).

Implementação concreta de RepositorioInquerito usando SQLAlchemy async.
Apenas este arquivo pode importar models SQLAlchemy — nunca domain/ nem application/.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.repositorio_inquerito import RepositorioInquerito
from domain.inquerito.entity import Inquerito, StatusInquerito
from domain.shared.exceptions import ConflitoError
from infrastructure.database.models import InqueritoModel, OcorrenciaModel


class InqueritoRepositorioSQLAlchemy(RepositorioInquerito):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._versoes_carregadas: dict[UUID, int] = {}

    async def _carregar_model(self, inquerito_id: UUID) -> InqueritoModel | None:
        stmt = (
            select(InqueritoModel)
            .where(InqueritoModel.id == inquerito_id)
            .options(selectinload(InqueritoModel.ocorrencias))
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def _verificar_versao(self, inquerito: Inquerito) -> None:
        stmt = select(InqueritoModel.versao).where(InqueritoModel.id == inquerito.id).with_for_update()
        versao_banco = (await self._session.execute(stmt)).scalar_one()
        versao_esperada = self._versoes_carregadas.get(inquerito.id, versao_banco)
        if versao_banco != versao_esperada or inquerito.versao < versao_banco:
            raise ConflitoError(
                "O inquérito foi alterado por outro usuário; recarregue e tente novamente.",
                chave="generic.versao_desatualizada",
                versao_atual=versao_banco,
            )

    async def salvar(self, inquerito: Inquerito) -> None:
        existente = await self._carregar_model(inquerito.id)
        if existente is None:
            model = InqueritoModel(
                id=inquerito.id,
                numero=inquerito.numero,
                ementa=inquerito.ementa,
                delegado_id=inquerito.delegado_id,
                status=inquerito.status.value,
                relatorio_final=inquerito.relatorio_final,
                motivo_arquivamento=inquerito.motivo_arquivamento,
                data_abertura=inquerito.data_abertura,
                concluido_em=inquerito.concluido_em,
                atualizado_em=inquerito.atualizado_em,
                ativo=inquerito.ativo,
                versao=inquerito.versao,
            )
            self._session.add(model)
        else:
            await self._verificar_versao(inquerito)
            existente.ementa = inquerito.ementa
            existente.status = inquerito.status.value
            existente.relatorio_final = inquerito.relatorio_final
            existente.motivo_arquivamento = inquerito.motivo_arquivamento
            existente.concluido_em = inquerito.concluido_em
            existente.atualizado_em = inquerito.atualizado_em
            existente.ativo = inquerito.ativo
            existente.versao = inquerito.versao
        await self._session.flush()
        self._versoes_carregadas[inquerito.id] = inquerito.versao

    async def buscar_por_id(self, inquerito_id: UUID) -> Inquerito | None:
        model = await self._carregar_model(inquerito_id)
        if model is None:
            return None
        self._versoes_carregadas[model.id] = model.versao
        return self._to_domain(model)

    async def buscar_por_numero(self, numero: str) -> Inquerito | None:
        stmt = (
            select(InqueritoModel)
            .where(InqueritoModel.numero == numero)
            .options(selectinload(InqueritoModel.ocorrencias))
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        self._versoes_carregadas[model.id] = model.versao
        return self._to_domain(model)

    async def listar(
        self,
        status: list[StatusInquerito] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Inquerito], int]:
        stmt = select(InqueritoModel).where(InqueritoModel.ativo.is_(True))
        if status:
            stmt = stmt.where(InqueritoModel.status.in_([s.value for s in status]))

        total = (await self._session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

        stmt = (
            stmt.options(selectinload(InqueritoModel.ocorrencias))
            .order_by(InqueritoModel.data_abertura.desc())
            .offset(offset)
            .limit(limit)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        for m in models:
            self._versoes_carregadas[m.id] = m.versao
        return [self._to_domain(m) for m in models], total

    @staticmethod
    def _to_domain(model: InqueritoModel) -> Inquerito:
        inq = Inquerito(
            id=model.id,
            numero=model.numero,
            ementa=model.ementa,
            delegado_id=model.delegado_id,
            status=StatusInquerito(model.status),
            data_abertura=aware(model.data_abertura),
            atualizado_em=aware(model.atualizado_em) if model.atualizado_em else None,
            concluido_em=aware(model.concluido_em) if model.concluido_em else None,
            relatorio_final=model.relatorio_final,
            motivo_arquivamento=model.motivo_arquivamento,
            ativo=model.ativo,
            versao=model.versao,
            ocorrencias_ids=[oc.id for oc in model.ocorrencias if oc.status != "EXCLUIDA"],
        )
        return inq
