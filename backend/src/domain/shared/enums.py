"""Conversão de texto da borda para enums do domínio (Python puro, RNF05)."""
from __future__ import annotations

from enum import Enum

from domain.shared.exceptions import ValorInvalidoError


def interpretar_enum[E: Enum](
    tipo: type[E],
    valor: E | str | None,
    chave: str,
    mensagem: str = "Valor inválido: {valor}",
    *,
    normalizar: bool = False,
) -> E:
    """Membro de ``tipo`` para ``valor``; inválido → ``ValorInvalidoError`` com a ``chave`` i18n.

    Com ``normalizar``, ignora espaços nas bordas e diferença de caixa (``" alta "`` → ``ALTA``).
    ``mensagem`` aceita o marcador ``{valor}``.
    """
    if isinstance(valor, tipo):
        return valor
    texto = (valor or "").strip().upper() if normalizar else valor
    try:
        return tipo(texto)
    except ValueError as exc:
        raise ValorInvalidoError(mensagem.format(valor=valor), chave=chave, valor=valor) from exc


def interpretar_enum_ou_padrao[E: Enum](tipo: type[E], valor: E | str | None, padrao: E) -> E:
    """Como ``interpretar_enum`` normalizado, mas valor ausente ou inválido vira ``padrao``.

    Só para dados gerados pelo próprio sistema; entrada de usuário deve usar ``interpretar_enum``.
    """
    if isinstance(valor, tipo):
        return valor
    try:
        return tipo((valor or "").strip().upper())
    except ValueError:
        return padrao
