"""Adapter de saída: HasherArgon2 (argon2id via argon2-cffi)."""
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from application.ports.outbound.hasher_senha import HasherSenha


class HasherArgon2(HasherSenha):
    def __init__(self) -> None:
        self._ph = PasswordHasher()

    def gerar_hash(self, senha: str) -> str:
        return self._ph.hash(senha)

    def verificar(self, senha: str, senha_hash: str) -> bool:
        try:
            return self._ph.verify(senha_hash, senha)
        except (VerifyMismatchError, VerificationError, ValueError):
            return False
