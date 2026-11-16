"""
Data Mapper para a entidade Usuario (HEX-03 / SRP).

Isola a lógica de conversão bidirecional entre Usuario (Domain) e UsuarioModel (SQLAlchemy).
"""
from __future__ import annotations

from domain.usuario.entity import Papel, Usuario
from infrastructure.database.models import UsuarioModel


class UsuarioMapper:
    """Mapeamento bidirecional entre a entidade Usuario e o modelo relacional UsuarioModel."""

    @staticmethod
    def atualizar_model(model: UsuarioModel, usuario: Usuario) -> None:
        model.nome = usuario.nome
        model.login = usuario.login
        model.senha_hash = usuario.senha_hash
        model.papel = usuario.papel.value
        model.ativo = usuario.ativo

    @classmethod
    def to_model(cls, usuario: Usuario) -> UsuarioModel:
        model = UsuarioModel(id=usuario.id)
        cls.atualizar_model(model, usuario)
        return model

    @staticmethod
    def to_domain(model: UsuarioModel) -> Usuario:
        return Usuario(
            id=model.id,
            nome=model.nome,
            login=model.login,
            senha_hash=model.senha_hash,
            papel=Papel(model.papel),
            ativo=model.ativo,
        )
