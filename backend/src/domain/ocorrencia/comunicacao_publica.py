"""
Regras do canal público de comunicação de ocorrência (Delegacia Online — RF01).

Diferente do registro pelo agente (que só confere formato e tamanho do documento — DEC-04),
o cidadão se identifica sozinho: exige-se a declaração de maioridade/veracidade e, quando o
documento é um CPF, os dígitos verificadores são conferidos. Puro Python.

O protocolo é sequencial e portanto adivinhável; a consulta pública exige também o código
de acompanhamento, secreto e entregue só ao cidadão no ato do registro. Guarda-se apenas o
seu hash SHA-256 (``secrets``/``hashlib``/``hmac`` são stdlib).
"""
import hashlib
import hmac
import secrets

from domain.ocorrencia.autenticidade import ALFABETO_CHAVE
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


TAMANHO_CODIGO_ACOMPANHAMENTO = 10


def gerar_codigo_acompanhamento() -> str:
    """Código digitável (sem 0/O/1/I), ~50 bits de entropia."""
    return "".join(secrets.choice(ALFABETO_CHAVE) for _ in range(TAMANHO_CODIGO_ACOMPANHAMENTO))


def normalizar_codigo_acompanhamento(codigo: str) -> str:
    return "".join(c for c in (codigo or "").upper() if c.isalnum())


def hash_codigo_acompanhamento(codigo: str) -> str:
    return hashlib.sha256(normalizar_codigo_acompanhamento(codigo).encode("utf-8")).hexdigest()


def codigo_acompanhamento_confere(codigo: str, hash_armazenado: str | None) -> bool:
    """Comparação em tempo constante; sem hash armazenado (registro policial) nunca confere."""
    if not hash_armazenado or not normalizar_codigo_acompanhamento(codigo):
        return False
    return hmac.compare_digest(hash_codigo_acompanhamento(codigo), hash_armazenado)
