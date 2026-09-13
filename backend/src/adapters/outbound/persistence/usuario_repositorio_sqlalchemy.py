"""Adapter de saída: UsuarioRepositorioSQLAlchemy (RF12)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from domain.usuario.entity import Papel, Usuario
from infrastructure.database.models import UsuarioModel


class UsuarioRepositorioSQLAlchemy(RepositorioUsuario):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def buscar_por_login(self, login: str) -> Usuario | None:
        model = (await self._session.execute(select(UsuarioModel).where(UsuarioModel.login == login.lower()))).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def buscar_por_id(self, usuario_id: UUID) -> Usuario | None:
        model = await self._session.get(UsuarioModel, usuario_id)
        return self._to_domain(model) if model else None

    async def salvar(self, usuario: Usuario) -> None:
        model = await self._session.get(UsuarioModel, usuario.id)
        if model is None:
            self._session.add(
                UsuarioModel(id=usuario.id, nome=usuario.nome, login=usuario.login, senha_hash=usuario.senha_hash, papel=usuario.papel.value, ativo=usuario.ativo)
            )
        else:
            model.nome, model.login, model.senha_hash, model.papel, model.ativo = (
                usuario.nome, usuario.login, usuario.senha_hash, usuario.papel.value, usuario.ativo,
            )
        await self._session.flush()

    async def listar(self) -> list[Usuario]:
        rows = (await self._session.execute(select(UsuarioModel).order_by(UsuarioModel.login))).scalars().all()
        return [self._to_domain(m) for m in rows]

    @staticmethod
    def _to_domain(m: UsuarioModel) -> Usuario:
        return Usuario(id=m.id, nome=m.nome, login=m.login, senha_hash=m.senha_hash, papel=Papel(m.papel), ativo=m.ativo)
