"""
Regras do canal público de comunicação de ocorrência (Delegacia Online — RF01).

Diferente do registro pelo agente (que só confere formato e tamanho do documento — DEC-04),
o cidadão se identifica sozinho: exige-se a declaração de maioridade/veracidade e, quando o
documento é um CPF, os dígitos verificadores são conferidos. Puro Python.
"""
from domain.shared.documentos import TAMANHO_CPF, cpf_valido, normalizar_cpf
from domain.shared.exceptions import ValorInvalidoError


def validar_comunicacao_publica(documento: str, declaracao_maioridade: bool) -> None:
    if not declaracao_maioridade:
        raise ValorInvalidoError(
            "Declaração de maioridade e veracidade não confirmada.", chave="ocorrencia.declaracao_maioridade_ausente"
        )
    digitos = normalizar_cpf(documento)
    if len(digitos) == TAMANHO_CPF and not cpf_valido(digitos):
        raise ValorInvalidoError("CPF do comunicante inválido.", chave="envolvido.cpf_comunicante_invalido")
