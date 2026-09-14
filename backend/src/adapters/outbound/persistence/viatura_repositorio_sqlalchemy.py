"""Adapter de saída: ViaturaRepositorioSQLAlchemy (RF15) com optimistic locking por ``versao``."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from domain.shared.exceptions import ConflitoError
from domain.shared.geo import Coordenada
from domain.viatura.entity import Posicao, SituacaoViatura, Viatura
from infrastructure.database.models import ViaturaModel


class ViaturaRepositorioSQLAlchemy(RepositorioViatura):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._versoes_carregadas: dict[UUID, int] = {}

    async def salvar(self, viatura: Viatura) -> None:
        model = await self._session.get(ViaturaModel, viatura.id)
        if model is None:
            model = ViaturaModel(id=viatura.id)
            self._session.add(model)
        else:
            stmt = select(ViaturaModel.versao).where(ViaturaModel.id == viatura.id).with_for_update()
            versao_banco = (await self._session.execute(stmt)).scalar_one()
            esperada = self._versoes_carregadas.get(viatura.id, versao_banco)
            if versao_banco != esperada or viatura.versao < versao_banco:
                raise ConflitoError("A viatura foi alterada por outro usuário.", chave="generic.versao_desatualizada", versao_atual=versao_banco)
        p = viatura.ultima_posicao
        model.prefixo, model.placa, model.situacao, model.versao, model.atualizada_em = (
            viatura.prefixo, viatura.placa, viatura.situacao.value, viatura.versao, viatura.atualizada_em,
        )
        model.latitude = p.coordenada.latitude if p else None
        model.longitude = p.coordenada.longitude if p else None
        model.posicao_registrada_em = p.registrada_em if p else None
        await self._session.flush()
        self._versoes_carregadas[viatura.id] = viatura.versao

    async def buscar_por_id(self, viatura_id: UUID) -> Viatura | None:
        model = await self._session.get(ViaturaModel, viatura_id)
        return self._to_domain(model) if model else None

    async def buscar_por_prefixo(self, prefixo: str) -> Viatura | None:
        model = (await self._session.execute(select(ViaturaModel).where(ViaturaModel.prefixo == prefixo.upper()))).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def buscar_por_placa(self, placa: str) -> Viatura | None:
        model = (await self._session.execute(select(ViaturaModel).where(ViaturaModel.placa == placa.upper()))).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def listar(self, situacoes: tuple[SituacaoViatura, ...] = ()) -> list[Viatura]:
        stmt = select(ViaturaModel).order_by(ViaturaModel.prefixo)
        if situacoes:
            stmt = stmt.where(ViaturaModel.situacao.in_([s.value for s in situacoes]))
        return [self._to_domain(m) for m in (await self._session.execute(stmt)).scalars().all()]

    def _to_domain(self, m: ViaturaModel) -> Viatura:
        posicao = None
        if m.latitude is not None and m.longitude is not None and m.posicao_registrada_em is not None:
            posicao = Posicao(coordenada=Coordenada(m.latitude, m.longitude), registrada_em=aware(m.posicao_registrada_em))
        self._versoes_carregadas[m.id] = m.versao
        return Viatura(
            id=m.id, prefixo=m.prefixo, placa=m.placa, situacao=SituacaoViatura(m.situacao), ultima_posicao=posicao,
            versao=m.versao, atualizada_em=aware(m.atualizada_em) if m.atualizada_em else None,
        )
