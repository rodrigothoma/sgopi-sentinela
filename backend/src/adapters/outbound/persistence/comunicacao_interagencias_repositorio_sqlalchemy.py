"""
Adapter de saída: Repositório de Comunicação Interagências (RF10 / UC10).
"""
from __future__ import annotations

from collections.abc import Collection
from uuid import UUID

from sqlalchemy import ColumnElement, String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.mappers import ComunicacaoInteragenciasMapper
from application.ports.outbound.repositorio_comunicacao_interagencias import RepositorioComunicacaoInteragencias
from domain.interagencias.entity import ComunicacaoInteragencias, NivelSigilo
from infrastructure.database.models import ComunicacaoInteragenciasModel

_ESCAPE_LIKE = "\\"


def _pertence_ao_departamento(departamento: str) -> ColumnElement[bool]:
    """Origem igual ao departamento ou departamento presente na lista JSON de destinatários.

    A lista é comparada pelo texto serializado (``["POLICIA_CIVIL", ...]``), o que funciona
    igual no PostgreSQL e no SQLite; ``_`` e ``%`` do código são escapados para o LIKE.
    """
    codigo = departamento.strip().upper()
    literal = codigo.replace(_ESCAPE_LIKE, _ESCAPE_LIKE * 2).replace("%", "\\%").replace("_", "\\_")
    modelo = ComunicacaoInteragenciasModel
    return or_(
        func.upper(modelo.departamento_origem) == codigo,
        cast(modelo.departamentos_destinatarios, String).like(f'%"{literal}"%', escape=_ESCAPE_LIKE),
    )


class ComunicacaoInteragenciasRepositorioSQLAlchemy(RepositorioComunicacaoInteragencias):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def salvar(self, comunicacao: ComunicacaoInteragencias) -> ComunicacaoInteragencias:
        stmt = select(ComunicacaoInteragenciasModel).where(ComunicacaoInteragenciasModel.id == comunicacao.id)
        existente = (await self._session.execute(stmt)).scalar_one_or_none()
        if existente is None:
            self._session.add(ComunicacaoInteragenciasMapper.to_model(comunicacao))
        else:
            ComunicacaoInteragenciasMapper.atualizar_model(existente, comunicacao)

        await self._session.flush()
        return comunicacao

    async def obter_por_id(self, comunicacao_id: UUID) -> ComunicacaoInteragencias | None:
        stmt = select(ComunicacaoInteragenciasModel).where(
            ComunicacaoInteragenciasModel.id == comunicacao_id,
            ComunicacaoInteragenciasModel.ativo.is_(True),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return ComunicacaoInteragenciasMapper.to_domain(model) if model else None

    async def listar(
        self,
        departamento: str | None = None,
        protocolo: str | None = None,
        remetente_id: UUID | None = None,
        limite: int = 50,
        niveis_sigilo: Collection[NivelSigilo] | None = None,
        visivel_ao_usuario: UUID | None = None,
    ) -> list[ComunicacaoInteragencias]:
        modelo = ComunicacaoInteragenciasModel
        stmt = select(modelo).where(modelo.ativo.is_(True))
        if protocolo:
            stmt = stmt.where(modelo.protocolo_ocorrencia == protocolo)
        if remetente_id:
            stmt = stmt.where(modelo.remetente_id == remetente_id)
        if departamento:
            stmt = stmt.where(_pertence_ao_departamento(departamento))
        if niveis_sigilo is not None:
            visivel = modelo.nivel_sigilo.in_([n.value for n in niveis_sigilo])
            if visivel_ao_usuario is not None:
                visivel = or_(visivel, modelo.remetente_id == visivel_ao_usuario)
            stmt = stmt.where(visivel)
        stmt = stmt.order_by(modelo.criada_em.desc()).limit(limite)
        models = (await self._session.execute(stmt)).scalars().all()
        return [ComunicacaoInteragenciasMapper.to_domain(m) for m in models]

    async def listar_respostas(self, mensagem_pai_id: UUID) -> list[ComunicacaoInteragencias]:
        stmt = (
            select(ComunicacaoInteragenciasModel)
            .where(
                ComunicacaoInteragenciasModel.mensagem_pai_id == mensagem_pai_id,
                ComunicacaoInteragenciasModel.ativo.is_(True),
            )
            .order_by(ComunicacaoInteragenciasModel.criada_em.asc())
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [ComunicacaoInteragenciasMapper.to_domain(m) for m in models]
