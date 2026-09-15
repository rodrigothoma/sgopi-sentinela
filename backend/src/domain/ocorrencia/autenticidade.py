"""
Autenticidade pública do documento oficial (RF08 / UC08).

Quando o Delegado valida a ocorrência, o Boletim de Ocorrência é considerado
emitido e recebe uma chave de segurança alfanumérica. A chave é pública por
natureza (vai impressa no documento / QR Code) e só permite conferir a
autenticidade — nunca revela dados pessoais (RNF02, LGPD).

Puro Python: ``secrets`` é stdlib, assim como ``uuid4`` já usado no domínio.
"""
from __future__ import annotations

import secrets
from enum import Enum

from domain.shared.exceptions import ValorInvalidoError

# Sem 0/O/1/I: a chave é digitada por humanos a partir de um documento impresso.
ALFABETO_CHAVE = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TAMANHO_CHAVE = 24
_TAMANHO_GRUPO = 4


class SituacaoDocumento(str, Enum):
    """Resultado da conferência pública (UC08 passo 5)."""

    VALIDO = "VALIDO"
    ADULTERADO = "ADULTERADO"


def gerar_chave_autenticidade() -> str:
    return "".join(secrets.choice(ALFABETO_CHAVE) for _ in range(TAMANHO_CHAVE))


def normalizar_chave(valor: str | None) -> str:
    """Aceita a chave como digitada (minúsculas, hífens, espaços) e devolve a forma canônica."""
    chave = "".join(c for c in (valor or "").upper() if c.isalnum())
    if len(chave) != TAMANHO_CHAVE or any(c not in ALFABETO_CHAVE for c in chave):
        raise ValorInvalidoError(
            f"Chave de autenticidade inválida; esperados {TAMANHO_CHAVE} caracteres.",
            chave="documento.chave_invalida",
            tamanho=TAMANHO_CHAVE,
        )
    return chave


def formatar_chave(chave: str) -> str:
    """XXXX-XXXX-XXXX-XXXX-XXXX-XXXX — forma legível para impressão e digitação."""
    return "-".join(chave[i : i + _TAMANHO_GRUPO] for i in range(0, len(chave), _TAMANHO_GRUPO))
