"""Eventos de auditoria de usuários, autenticação e controle de acesso (RNF02 · RNF03)."""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar, Self
from uuid import UUID

from domain.auditoria.evento import EventoAuditoria
from domain.usuario.entity import Papel, Usuario

ENTIDADE_USUARIO = "Usuario"


# ------------------------------------------------------------- gestão do efetivo
@dataclass(frozen=True, kw_only=True)
class EventoGestaoUsuario(EventoAuditoria):
    """Alteração feita por um gestor numa conta; o login do alvo vai sempre junto."""

    ENTIDADE: ClassVar[str] = ENTIDADE_USUARIO

    usuario_id: UUID
    login: str

    def id_entidade(self) -> str | None:
        return str(self.usuario_id)

    @abstractmethod
    def _alteracao(self) -> dict[str, Any]:
        """O que mudou na conta (o ``login`` é acrescentado pela classe base)."""

    def dados_depois(self) -> dict[str, Any] | None:
        return {"login": self.login, **self._alteracao()}


@dataclass(frozen=True, kw_only=True)
class UsuarioCadastrado(EventoGestaoUsuario):
    OPERACAO: ClassVar[str] = "usuario.cadastrar"

    nome: str
    papel: str

    @classmethod
    def de(cls, usuario: Usuario) -> Self:
        return cls(usuario_id=usuario.id, login=usuario.login, nome=usuario.nome, papel=usuario.papel.value)

    def _alteracao(self) -> dict[str, Any]:
        return {"nome": self.nome, "papel": self.papel, "ativo": True}


@dataclass(frozen=True, kw_only=True)
class PapelUsuarioAlterado(EventoGestaoUsuario):
    OPERACAO: ClassVar[str] = "usuario.alterar_papel"

    papel_antes: str
    papel: str

    @classmethod
    def de(cls, usuario: Usuario, anterior: Papel) -> Self:
        return cls(usuario_id=usuario.id, login=usuario.login, papel_antes=anterior.value, papel=usuario.papel.value)

    def dados_antes(self) -> dict[str, Any] | None:
        return {"papel": self.papel_antes}

    def _alteracao(self) -> dict[str, Any]:
        return {"papel": self.papel}


@dataclass(frozen=True, kw_only=True)
class SituacaoUsuarioAlterada(EventoGestaoUsuario):
    """Desativação ou reativação da conta, com motivo opcional."""

    ATIVO_DEPOIS: ClassVar[bool]

    motivo: str | None

    @classmethod
    def de(cls, usuario: Usuario, motivo: str | None) -> Self:
        return cls(usuario_id=usuario.id, login=usuario.login, motivo=(motivo or "").strip() or None)

    def dados_antes(self) -> dict[str, Any] | None:
        return {"ativo": not self.ATIVO_DEPOIS}

    def _alteracao(self) -> dict[str, Any]:
        return {"ativo": self.ATIVO_DEPOIS, "motivo": self.motivo}


@dataclass(frozen=True, kw_only=True)
class UsuarioDesativado(SituacaoUsuarioAlterada):
    OPERACAO: ClassVar[str] = "usuario.desativar"
    ATIVO_DEPOIS: ClassVar[bool] = False


@dataclass(frozen=True, kw_only=True)
class UsuarioReativado(SituacaoUsuarioAlterada):
    OPERACAO: ClassVar[str] = "usuario.reativar"
    ATIVO_DEPOIS: ClassVar[bool] = True


# --------------------------------------------------------------------- autenticação
@dataclass(frozen=True, kw_only=True)
class LoginRealizado(EventoAuditoria):
    OPERACAO: ClassVar[str] = "auth.login"
    ENTIDADE: ClassVar[str] = ENTIDADE_USUARIO

    usuario_id: UUID
    papel: str

    @classmethod
    def de(cls, usuario: Usuario) -> Self:
        return cls(usuario_id=usuario.id, papel=usuario.papel.value)

    def id_entidade(self) -> str | None:
        return str(self.usuario_id)

    def dados_depois(self) -> dict[str, Any] | None:
        return {"papel": self.papel}


@dataclass(frozen=True, kw_only=True)
class TentativaDeLoginRecusada(EventoAuditoria):
    """Sem autor (quem tentou é desconhecido): identifica pelo login digitado e, se a conta
    existe, aponta o usuário-alvo."""

    ENTIDADE: ClassVar[str] = ENTIDADE_USUARIO

    login: str
    usuario_alvo_id: UUID | None

    def id_entidade(self) -> str | None:
        return self.login or None

    @abstractmethod
    def _detalhe(self) -> dict[str, Any]: ...

    def dados_depois(self) -> dict[str, Any] | None:
        alvo = {"usuario_alvo_id": str(self.usuario_alvo_id)} if self.usuario_alvo_id else {}
        return {**self._detalhe(), **alvo}


@dataclass(frozen=True, kw_only=True)
class LoginNegado(TentativaDeLoginRecusada):
    OPERACAO: ClassVar[str] = "auth.login_negado"

    motivo: str

    def _detalhe(self) -> dict[str, Any]:
        return {"motivo": self.motivo}


@dataclass(frozen=True, kw_only=True)
class LoginBloqueado(TentativaDeLoginRecusada):
    OPERACAO: ClassVar[str] = "auth.login_bloqueado"

    bloqueado_ate: datetime

    def _detalhe(self) -> dict[str, Any]:
        return {"bloqueado_ate": self.bloqueado_ate.isoformat()}


# ---------------------------------------------------------------- controle de acesso
@dataclass(frozen=True, kw_only=True)
class AcessoNegado(EventoAuditoria):
    """Papel sem permissão tentou usar uma rota protegida."""

    OPERACAO: ClassVar[str] = "auth.acesso_negado"
    ENTIDADE: ClassVar[str] = "Rota"

    rota: str
    papel: Papel
    exigido: tuple[Papel, ...]

    def id_entidade(self) -> str | None:
        return self.rota

    def dados_depois(self) -> dict[str, Any] | None:
        return {"papel": self.papel.value, "exigido": [p.value for p in self.exigido]}
