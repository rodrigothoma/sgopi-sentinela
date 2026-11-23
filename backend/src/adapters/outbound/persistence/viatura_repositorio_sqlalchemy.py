"""Adapter de saída: ViaturaRepositorioSQLAlchemy (RF02) com optimistic locking por ``versao``."""
from __future__ import annotations

from sqlalchemy import select

from adapters.outbound.persistence._concorrencia import RepositorioVersionadoSQLAlchemy
from adapters.outbound.persistence.mappers import ViaturaMapper
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from domain.viatura.entity import SituacaoViatura, Viatura
from infrastructure.database.models import ViaturaModel


class ViaturaRepositorioSQLAlchemy(
    RepositorioVersionadoSQLAlchemy[ViaturaModel, Viatura],
    RepositorioViatura,
):
    """Repositório de viaturas policiais com persistência relacional via SQLAlchemy async."""

    _model_cls = ViaturaModel
    _mapper_cls = ViaturaMapper
    _mensagem_conflito = "A viatura foi alterada por outro usuário; recarregue e tente novamente."

    async def buscar_por_prefixo(self, prefixo: str) -> Viatura | None:
        """Localiza viatura pelo prefixo tático oficial (ex: 'V-01', case-insensitive)."""
        model = (await self._session.execute(select(ViaturaModel).where(ViaturaModel.prefixo == prefixo.upper()))).scalar_one_or_none()
        return self._reconstituir(model)

    async def buscar_por_placa(self, placa: str) -> Viatura | None:
        """Localiza viatura pela placa veicular oficial."""
        model = (await self._session.execute(select(ViaturaModel).where(ViaturaModel.placa == placa.upper()))).scalar_one_or_none()
        return self._reconstituir(model)

    async def listar(self, situacoes: tuple[SituacaoViatura, ...] = ()) -> list[Viatura]:
        """Lista viaturas ordenadas por prefixo, com filtro opcional por situação operacional."""
        stmt = select(ViaturaModel).where(ViaturaModel.ativo.is_(True)).order_by(ViaturaModel.prefixo)
        if situacoes:
            stmt = stmt.where(ViaturaModel.situacao.in_([s.value for s in situacoes]))
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._reconstituir(m) for m in models]
