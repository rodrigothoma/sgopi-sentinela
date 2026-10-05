"""
Entidade Usuario e enum Papel (RNF02 / DEC-08).

Papéis do MVP: AGENTE, DELEGADO, OPERADOR_CENTRAL. Os demais existem no enum
sem caso de uso associado. Não há acesso anônimo no MVP: a comunicação pública
(Delegacia Online) é registrada em nome de um usuário de sistema com papel CIDADAO,
inativo e sem senha utilizável — nunca autentica e nunca se confunde com um policial.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from domain.shared.exceptions import CampoObrigatorioError, ConflitoError, ValorInvalidoError


class Papel(str, Enum):
    AGENTE = "AGENTE"
    DELEGADO = "DELEGADO"
    OPERADOR_CENTRAL = "OPERADOR_CENTRAL"
    SUPERVISOR = "SUPERVISOR"
    PERITO = "PERITO"
    ESCRIVAO = "ESCRIVAO"
    CIDADAO = "CIDADAO"


LOGIN_SISTEMA_CIDADAO = "sistema.cidadao"
NOME_SISTEMA_CIDADAO = "Delegacia Online (comunicação do cidadão)"
# Sugestão #13: login de 3 a 50 caracteres (minúsculas, dígitos, ponto, hífen e sublinhado)
_LOGIN_VALIDO = re.compile(r"^[a-z0-9._-]{3,50}$")
TAMANHO_MINIMO_SENHA = 8
# Papel técnico do canal público: nunca atribuído nem gerido pela tela de usuários
PAPEIS_ATRIBUIVEIS = tuple(p for p in Papel if p is not Papel.CIDADAO)

# Não é um hash Argon2 válido: nenhuma senha confere (e usuário inativo nem chega a ser verificado).
SENHA_HASH_INUTILIZAVEL = "!"


@dataclass
class Usuario:
    nome: str
    login: str
    senha_hash: str
    papel: Papel
    ativo: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise CampoObrigatorioError("Nome do usuário é obrigatório.", chave="usuario.nome_vazio")
        if not self.login or not self.login.strip():
            raise CampoObrigatorioError("Login é obrigatório.", chave="usuario.login_vazio")
        if not self.senha_hash:
            raise CampoObrigatorioError("Hash de senha é obrigatório.", chave="usuario.senha_vazia")
        self.login = self.login.strip().lower()

    @classmethod
    def cadastrar(cls, *, nome: str, login: str, senha_hash: str, papel: Papel) -> Usuario:
        """Novo membro do efetivo, já ativo (sugestão #13). Login normalizado e validado."""
        _exigir_papel_atribuivel(papel)
        login_normalizado = (login or "").strip().lower()
        if not _LOGIN_VALIDO.match(login_normalizado):
            raise ValorInvalidoError(
                "Login deve ter de 3 a 50 caracteres: letras minúsculas, dígitos, ponto, hífen ou sublinhado.",
                chave="usuario.login_invalido",
            )
        return cls(nome=nome.strip(), login=login_normalizado, senha_hash=senha_hash, papel=papel)

    def alterar_papel(self, novo: Papel) -> Papel:
        """Troca o papel e devolve o anterior (para a auditoria)."""
        self._exigir_gerenciavel()
        _exigir_papel_atribuivel(novo)
        if novo == self.papel:
            raise ValorInvalidoError("O usuário já tem esse papel.", chave="usuario.papel_inalterado")
        anterior, self.papel = self.papel, novo
        return anterior

    def desativar(self) -> None:
        """Retirada lógica (AGENTS.md §5): ``ativo = False``, nunca DELETE."""
        self._exigir_gerenciavel()
        if not self.ativo:
            raise ConflitoError("O usuário já está inativo.", chave="usuario.ja_inativo")
        self.ativo = False

    def reativar(self) -> None:
        self._exigir_gerenciavel()
        if self.ativo:
            raise ConflitoError("O usuário já está ativo.", chave="usuario.ja_ativo")
        self.ativo = True

    def _exigir_gerenciavel(self) -> None:
        if self.papel == Papel.CIDADAO:
            raise ValorInvalidoError("O usuário de sistema do canal público não é gerenciável.", chave="usuario.sistema")

    @classmethod
    def sistema_cidadao(cls) -> Usuario:
        """Autor técnico das comunicações públicas: papel CIDADAO, inativo, sem senha."""
        return cls(
            nome=NOME_SISTEMA_CIDADAO,
            login=LOGIN_SISTEMA_CIDADAO,
            senha_hash=SENHA_HASH_INUTILIZAVEL,
            papel=Papel.CIDADAO,
            ativo=False,
        )


def _exigir_papel_atribuivel(papel: Papel) -> None:
    if papel not in PAPEIS_ATRIBUIVEIS:
        raise ValorInvalidoError(f"Papel {papel.value} não pode ser atribuído.", chave="usuario.papel_invalido")


def interpretar_papel(valor: str) -> Papel:
    """Texto da borda → ``Papel`` atribuível."""
    try:
        papel = Papel((valor or "").strip().upper())
    except ValueError as exc:
        raise ValorInvalidoError(f"Papel inválido: {valor}", chave="usuario.papel_invalido") from exc
    _exigir_papel_atribuivel(papel)
    return papel
