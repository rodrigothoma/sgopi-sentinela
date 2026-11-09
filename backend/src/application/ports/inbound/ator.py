"""
DTO transversal: Ator — quem executa o caso de uso (vem do token JWT, nunca do body).
"""
from dataclasses import dataclass
from uuid import UUID

from domain.shared.exceptions import AcessoNegadoError
from domain.usuario.entity import Papel
from domain.usuario.permissoes import Permissao, papeis_com, tem_permissao


@dataclass(frozen=True)
class Ator:
    id: UUID
    login: str
    papel: Papel
    ip: str | None = None

    def exigir_papel(self, *papeis: Papel) -> None:
        """Defesa em profundidade: o caso de uso re-verifica o papel (RNF02)."""
        if self.papel not in papeis:
            raise AcessoNegadoError(
                f"Papel {self.papel.value} não autorizado; exigido: {', '.join(p.value for p in papeis)}.",
                papel=self.papel.value,
                exigido=[p.value for p in papeis],
            )

    def pode(self, permissao: Permissao) -> bool:
        return tem_permissao(self.papel, permissao)

    def exigir(self, permissao: Permissao, mensagem: str = "", chave: str | None = None) -> None:
        """Defesa em profundidade pelo catálogo de permissões; ``mensagem``/``chave`` específicas do caso de uso."""
        if self.pode(permissao):
            return
        exigido = [p.value for p in papeis_com(permissao)]
        raise AcessoNegadoError(
            mensagem or f"Papel {self.papel.value} não autorizado; exigido: {', '.join(exigido)}.",
            chave=chave,
            papel=self.papel.value,
            exigido=exigido,
        )
