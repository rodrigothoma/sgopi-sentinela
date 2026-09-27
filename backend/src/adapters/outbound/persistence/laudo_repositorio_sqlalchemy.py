"""
Adapter de saída: LaudoRepositorioSQLAlchemy (RF07 / UC07).

Implementação concreta de RepositorioLaudoPericial usando SQLAlchemy async.
Apenas este arquivo pode importar models SQLAlchemy — nunca domain/ nem application/.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.repositorio_laudo import RepositorioLaudoPericial
from domain.laudo.entity import LaudoPericial, StatusLaudo, TipoPericia
from domain.shared.exceptions import ConflitoError
from infrastructure.database.models import LaudoPericialModel


class LaudoRepositorioSQLAlchemy(RepositorioLaudoPericial):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._versoes_carregadas: dict[UUID, int] = {}

    async def _carregar_model(self, laudo_id: UUID) -> LaudoPericialModel | None:
        stmt = select(LaudoPericialModel).where(LaudoPericialModel.id == laudo_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def _verificar_versao(self, laudo: LaudoPericial) -> None:
        stmt = select(LaudoPericialModel.versao).where(LaudoPericialModel.id == laudo.id).with_for_update()
        versao_banco = (await self._session.execute(stmt)).scalar_one()
        versao_esperada = self._versoes_carregadas.get(laudo.id, versao_banco)
        if versao_banco != versao_esperada or laudo.versao < versao_banco:
            raise ConflitoError(
                "O laudo pericial foi alterado por outro usuário; recarregue e tente novamente.",
                chave="generic.versao_desatualizada",
                versao_atual=versao_banco,
            )

    async def salvar(self, laudo: LaudoPericial) -> None:
        existente = await self._carregar_model(laudo.id)
        if existente is None:
            model = LaudoPericialModel(
                id=laudo.id,
                numero_referencia=laudo.numero_referencia,
                tipo_pericia=laudo.tipo_pericia.value,
                descricao_solicitacao=laudo.descricao_solicitacao,
                solicitante_id=laudo.solicitante_id,
                perito_id=laudo.perito_id,
                ocorrencia_id=laudo.ocorrencia_id,
                inquerito_id=laudo.inquerito_id,
                item_apreendido_id=laudo.item_apreendido_id,
                conclusoes_tecnicas=laudo.conclusoes_tecnicas,
                arquivo_chave=laudo.arquivo_chave,
                arquivo_nome=laudo.arquivo_nome,
                hash_sha256=laudo.hash_sha256,
                status=laudo.status.value,
                solicitado_em=laudo.solicitado_em,
                concluido_em=laudo.concluido_em,
                atualizado_em=laudo.atualizado_em,
                ativo=laudo.ativo,
                versao=laudo.versao,
            )
            self._session.add(model)
        else:
            await self._verificar_versao(laudo)
            existente.perito_id = laudo.perito_id
            existente.conclusoes_tecnicas = laudo.conclusoes_tecnicas
            existente.arquivo_chave = laudo.arquivo_chave
            existente.arquivo_nome = laudo.arquivo_nome
            existente.hash_sha256 = laudo.hash_sha256
            existente.status = laudo.status.value
            existente.concluido_em = laudo.concluido_em
            existente.atualizado_em = laudo.atualizado_em
            existente.ativo = laudo.ativo
            existente.versao = laudo.versao
        await self._session.flush()
        self._versoes_carregadas[laudo.id] = laudo.versao

    async def buscar_por_id(self, laudo_id: UUID) -> LaudoPericial | None:
        model = await self._carregar_model(laudo_id)
        if model is None:
            return None
        self._versoes_carregadas[model.id] = model.versao
        return self._to_domain(model)

    async def buscar_por_referencia(self, numero_referencia: str) -> LaudoPericial | None:
        stmt = select(LaudoPericialModel).where(LaudoPericialModel.numero_referencia == numero_referencia)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        self._versoes_carregadas[model.id] = model.versao
        return self._to_domain(model)

    async def listar(
        self,
        status: list[StatusLaudo] | None = None,
        ocorrencia_id: UUID | None = None,
        inquerito_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[LaudoPericial], int]:
        stmt = select(LaudoPericialModel).where(LaudoPericialModel.ativo.is_(True))
        if status:
            stmt = stmt.where(LaudoPericialModel.status.in_([s.value for s in status]))
        if ocorrencia_id:
            stmt = stmt.where(LaudoPericialModel.ocorrencia_id == ocorrencia_id)
        if inquerito_id:
            stmt = stmt.where(LaudoPericialModel.inquerito_id == inquerito_id)

        total = (await self._session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

        stmt = stmt.order_by(LaudoPericialModel.solicitado_em.desc()).offset(offset).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        for m in models:
            self._versoes_carregadas[m.id] = m.versao
        return [self._to_domain(m) for m in models], total

    @staticmethod
    def _to_domain(model: LaudoPericialModel) -> LaudoPericial:
        return LaudoPericial(
            id=model.id,
            numero_referencia=model.numero_referencia,
            tipo_pericia=TipoPericia(model.tipo_pericia),
            descricao_solicitacao=model.descricao_solicitacao,
            solicitante_id=model.solicitante_id,
            perito_id=model.perito_id,
            ocorrencia_id=model.ocorrencia_id,
            inquerito_id=model.inquerito_id,
            item_apreendido_id=model.item_apreendido_id,
            conclusoes_tecnicas=model.conclusoes_tecnicas,
            arquivo_chave=model.arquivo_chave,
            arquivo_nome=model.arquivo_nome,
            hash_sha256=model.hash_sha256,
            status=StatusLaudo(model.status),
            solicitado_em=aware(model.solicitado_em),
            concluido_em=aware(model.concluido_em) if model.concluido_em else None,
            atualizado_em=aware(model.atualizado_em) if model.atualizado_em else None,
            ativo=model.ativo,
            versao=model.versao,
        )
