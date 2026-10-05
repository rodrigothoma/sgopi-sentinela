"""
Entidade Usuario e enum Papel (RNF02 / DEC-08).

Papéis do MVP: AGENTE, DELEGADO, OPERADOR_CENTRAL. Os demais existem no enum
sem caso de uso associado. Não há acesso anônimo no MVP: a comunicação pública
(Delegacia Online) é registrada em nome de um usuário de sistema com papel CIDADAO,
inativo e sem senha utilizável — nunca autentica e nunca se confunde com um policial.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from domain.shared.exceptions import CampoObrigatorioError


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
    def sistema_cidadao(cls) -> Usuario:
        """Autor técnico das comunicações públicas: papel CIDADAO, inativo, sem senha."""
        return cls(
            nome=NOME_SISTEMA_CIDADAO,
            login=LOGIN_SISTEMA_CIDADAO,
            senha_hash=SENHA_HASH_INUTILIZAVEL,
            papel=Papel.CIDADAO,
            ativo=False,
        )
