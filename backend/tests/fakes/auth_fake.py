"""Fakes de autenticação: RepositorioUsuarioFake, HasherFake, ProvedorTokenFake."""
from datetime import datetime, timedelta
from uuid import UUID

from application.ports.outbound.hasher_senha import HasherSenha
from application.ports.outbound.provedor_token import DadosToken, ProvedorToken
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from domain.shared.exceptions import CredenciaisInvalidasError
from domain.usuario.entity import Papel, Usuario


class RepositorioUsuarioFake(RepositorioUsuario):
    def __init__(self) -> None:
        self._store: dict[UUID, Usuario] = {}

    async def buscar_por_login(self, login: str) -> Usuario | None:
        return next((u for u in self._store.values() if u.login == login.lower()), None)

    async def buscar_por_id(self, usuario_id: UUID) -> Usuario | None:
        return self._store.get(usuario_id)

    async def salvar(self, usuario: Usuario) -> None:
        self._store[usuario.id] = usuario

    async def listar(self) -> list[Usuario]:
        return list(self._store.values())


class HasherFake(HasherSenha):
    """Hash reversível só para testes — nunca usar fora deles."""

    def gerar_hash(self, senha: str) -> str:
        return f"hash::{senha}"

    def verificar(self, senha: str, senha_hash: str) -> bool:
        return senha_hash == f"hash::{senha}"


class ProvedorTokenFake(ProvedorToken):
    def __init__(self, validade_horas: int = 8) -> None:
        self._validade = timedelta(hours=validade_horas)
        self._emitidos: dict[str, DadosToken] = {}

    def emitir(self, usuario_id: UUID, login: str, papel: Papel, agora: datetime) -> tuple[str, datetime]:
        expira = agora + self._validade
        token = f"tok-{login}-{len(self._emitidos)}"
        self._emitidos[token] = DadosToken(usuario_id=usuario_id, login=login, papel=papel, expira_em=expira)
        return token, expira

    def decodificar(self, token: str, agora: datetime) -> DadosToken:
        dados = self._emitidos.get(token)
        if dados is None or dados.expira_em <= agora:
            raise CredenciaisInvalidasError("Token inválido.", chave="auth.token_invalido")
        return dados
