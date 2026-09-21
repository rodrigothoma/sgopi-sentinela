"""
Autenticidade pública do documento oficial (RF08 / UC08).

Quando o Delegado valida a ocorrência, o Boletim de Ocorrência é considerado
emitido: a narrativa é congelada por hash SHA-256 (DEC-09) e o documento recebe
uma chave de segurança alfanumérica. A chave é pública por natureza (vai
impressa no comprovante e codificada no QR Code) e só permite conferir a
autenticidade — nunca revela dados pessoais (RNF02, LGPD).

O consulente pode informar a chave de 24 caracteres ou o próprio hash SHA-256
de verificação impresso no documento (UC08 passo 2). Puro Python: ``secrets``
é stdlib, assim como ``uuid4`` já usado no domínio.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from enum import Enum

from domain.shared.exceptions import ValorInvalidoError

# Sem 0/O/1/I: a chave é digitada por humanos a partir de um documento impresso.
ALFABETO_CHAVE = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TAMANHO_CHAVE = 24
TAMANHO_HASH = 64
_TAMANHO_GRUPO = 4
_HEXADECIMAL = "0123456789abcdef"


class SituacaoDocumento(str, Enum):
    """Resultado da conferência pública (UC08 passo 5)."""

    AUTENTICO = "AUTENTICO"
    ADULTERADO = "ADULTERADO"
    INDISPONIVEL = "INDISPONIVEL"


class TipoCodigoVerificacao(str, Enum):
    """Forma pela qual o consulente identificou o documento."""

    CHAVE = "CHAVE"
    HASH = "HASH"


@dataclass(frozen=True)
class CodigoVerificacao:
    """Código informado pelo consulente, já na forma canônica."""

    tipo: TipoCodigoVerificacao
    valor: str


def gerar_chave_autenticidade() -> str:
    return "".join(secrets.choice(ALFABETO_CHAVE) for _ in range(TAMANHO_CHAVE))


def _somente_alfanumericos(valor: str | None) -> str:
    return "".join(c for c in (valor or "") if c.isalnum())


def interpretar_codigo(valor: str | None) -> CodigoVerificacao:
    """
    Aceita o código como digitado (minúsculas, hífens, espaços) e o classifica:
    24 caracteres do alfabeto da chave → CHAVE; 64 hexadecimais → HASH SHA-256.
    """
    bruto = _somente_alfanumericos(valor)
    if len(bruto) == TAMANHO_HASH and all(c in _HEXADECIMAL for c in bruto.lower()):
        return CodigoVerificacao(TipoCodigoVerificacao.HASH, bruto.lower())
    chave = bruto.upper()
    if len(chave) == TAMANHO_CHAVE and all(c in ALFABETO_CHAVE for c in chave):
        return CodigoVerificacao(TipoCodigoVerificacao.CHAVE, chave)
    raise ValorInvalidoError(
        f"Código de verificação inválido; esperados {TAMANHO_CHAVE} caracteres da chave ou {TAMANHO_HASH} do hash.",
        chave="documento.codigo_invalido",
        tamanho_chave=TAMANHO_CHAVE,
        tamanho_hash=TAMANHO_HASH,
    )


def formatar_chave(chave: str) -> str:
    """XXXX-XXXX-XXXX-XXXX-XXXX-XXXX — forma legível para impressão e digitação."""
    return "-".join(chave[i : i + _TAMANHO_GRUPO] for i in range(0, len(chave), _TAMANHO_GRUPO))
