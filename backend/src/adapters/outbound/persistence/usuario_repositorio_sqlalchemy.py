"""Adapter de saída: UsuarioRepositorioSQLAlchemy (RNF02)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.mappers import UsuarioMapper
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from domain.usuario.entity import Usuario
from infrastructure.database.models import UsuarioModel


class UsuarioRepositorioSQLAlchemy(RepositorioUsuario):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def buscar_por_login(self, login: str) -> Usuario | None:
        stmt = select(UsuarioModel).where(UsuarioModel.login == login.lower())
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return UsuarioMapper.to_domain(model) if model else None

    async def buscar_por_id(self, usuario_id: UUID) -> Usuario | None:
        model = await self._session.get(UsuarioModel, usuario_id)
        return UsuarioMapper.to_domain(model) if model else None

    async def salvar(self, usuario: Usuario) -> None:
        model = await self._session.get(UsuarioModel, usuario.id)
        if model is None:
            self._session.add(UsuarioMapper.to_model(usuario))
        else:
            UsuarioMapper.atualizar_model(model, usuario)
        await self._session.flush()

    async def listar(self) -> list[Usuario]:
        rows = (await self._session.execute(select(UsuarioModel).order_by(UsuarioModel.login))).scalars().all()
        return [UsuarioMapper.to_domain(m) for m in rows]

