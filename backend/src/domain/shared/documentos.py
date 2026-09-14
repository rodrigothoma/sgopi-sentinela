"""
Validação de documentos pessoais (CPF). Puro Python.
"""
import re

from domain.shared.exceptions import ValorInvalidoError

_APENAS_DIGITOS = re.compile(r"\D")
_SEPARADORES = re.compile(r"[.\-/\s]")
_SO_DIGITOS_ASCII = re.compile(r"^[0-9]+$")

# Tamanhos fixos (somente dígitos): CPF nacional; RG no padrão do RS (10 dígitos).
TAMANHO_CPF = 11
TAMANHO_RG = 10


def normalizar_cpf(valor: str) -> str:
    return _APENAS_DIGITOS.sub("", valor)


def cpf_valido(valor: str) -> bool:
    """Confere os dois dígitos verificadores do CPF (rejeita sequências repetidas)."""
    cpf = normalizar_cpf(valor)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(cpf[tamanho]):
            return False
    return True


def validar_documento(valor: str | None) -> str | None:
    """
    Documento é opcional (DEC-04). Só dígitos são aceitos (pontuação de máscara é
    tolerada) e o tamanho é fixo: 11 dígitos = CPF, 10 dígitos = RG. Qualquer outro
    tamanho ou a presença de letras é rejeitada. Os dígitos verificadores do CPF NÃO
    são conferidos (decisão de produto: só formato e tamanho); ``cpf_valido`` fica
    disponível para quem precisar da conferência.
    """
    if valor is None:
        return None
    valor = valor.strip()
    if not valor:
        return None
    if not _SO_DIGITOS_ASCII.match(_SEPARADORES.sub("", valor)):
        raise ValorInvalidoError(
            f"Documento deve conter apenas números: {valor}", chave="envolvido.documento_nao_numerico"
        )
    digitos = normalizar_cpf(valor)
    if len(digitos) in (TAMANHO_CPF, TAMANHO_RG):
        return valor
    raise ValorInvalidoError(
        f"Documento com tamanho inválido ({len(digitos)} dígitos): {valor}",
        chave="envolvido.documento_tamanho_invalido",
        rg=TAMANHO_RG,
        cpf=TAMANHO_CPF,
    )


def mascarar_cpf(valor: str | None) -> str | None:
    """Máscara LGPD (RNF10): ***.***.789-** — preserva só o terceiro bloco."""
    if valor is None:
        return None
    digitos = normalizar_cpf(valor)
    if len(digitos) != 11:
        return "***"
    return f"***.***.{digitos[6:9]}-**"
