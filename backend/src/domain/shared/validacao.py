"""Validações de entrada reutilizadas pelas entidades (Python puro, RNF05)."""
from __future__ import annotations

from domain.shared.exceptions import CampoObrigatorioError, DomainError


def exigir_texto(
    valor: str | None,
    mensagem: str,
    chave: str | None = None,
    minimo: int = 1,
    erro: type[DomainError] = CampoObrigatorioError,
) -> str:
    """Devolve o texto sem espaços nas bordas; recusa vazio ou com menos de ``minimo`` caracteres."""
    texto = valor.strip() if valor else ""
    if len(texto) < minimo:
        raise erro(mensagem, chave=chave)
    return texto
