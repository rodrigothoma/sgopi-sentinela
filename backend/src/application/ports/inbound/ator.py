"""
DTO transversal: Ator — quem executa o caso de uso (vem do token JWT, nunca do body).
"""
from dataclasses import dataclass
from uuid import UUID

from domain.shared.exceptions import AcessoNegadoError
from domain.usuario.entity import Papel


@dataclass(frozen=True)
class Ator:
    id: UUID
    login: str
    papel: Papel
    ip: str | None = None

    def exigir_papel(self, *papeis: Papel) -> None:
        """Defesa em profundidade: o caso de uso re-verifica o papel (RF12)."""
        if self.papel not in papeis:
            raise AcessoNegadoError(
                f"Papel {self.papel.value} não autorizado; exigido: {', '.join(p.value for p in papeis)}.",
                papel=self.papel.value,
                exigido=[p.value for p in papeis],
            )
