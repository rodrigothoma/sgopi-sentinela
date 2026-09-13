"""
Validação de documentos pessoais (CPF). Puro Python.
"""
import re

from domain.shared.exceptions import ValorInvalidoError

_APENAS_DIGITOS = re.compile(r"\D")


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
    Documento é opcional (DEC-04). Se contiver 11 dígitos é tratado como CPF e
    precisa ser válido; outros formatos (RG etc.) são aceitos como texto livre.
    """
    if valor is None:
        return None
    valor = valor.strip()
    if not valor:
        return None
    digitos = normalizar_cpf(valor)
    if len(digitos) == 11 and not cpf_valido(digitos):
        raise ValorInvalidoError(f"CPF inválido: {valor}", chave="envolvido.cpf_invalido")
    return valor


def mascarar_cpf(valor: str | None) -> str | None:
    """Máscara LGPD (RNF10): ***.***.789-** — preserva só o terceiro bloco."""
    if valor is None:
        return None
    digitos = normalizar_cpf(valor)
    if len(digitos) != 11:
        return "***"
    return f"***.***.{digitos[6:9]}-**"
