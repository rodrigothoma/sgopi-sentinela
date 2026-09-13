"""
Entidade Usuario e enum Papel (RF12 / DEC-08).

Papéis do MVP: AGENTE, DELEGADO, OPERADOR_CENTRAL. Os demais existem no enum
sem caso de uso associado. Não há acesso anônimo no MVP.
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
