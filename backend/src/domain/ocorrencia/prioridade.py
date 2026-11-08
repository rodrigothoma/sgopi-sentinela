"""
Prioridade (gravidade) da ocorrência — sugestão #7 (RF01/RF04/RF02). Puro Python.

A prioridade é **sugerida** por uma tabela de regras sobre a natureza e as tipificações
(texto normalizado, sem acento) e pode ser ajustada pelo Agente no registro e pelo
Delegado na revisão. A fila do Delegado e o despacho automático atendem primeiro as
de maior ``peso``.
"""
from __future__ import annotations

import unicodedata
from collections.abc import Iterable

from domain.shared.enums import interpretar_enum
from domain.shared.prioridade import Prioridade

# Mesma escala dos ofícios interagências (domain/shared/prioridade.py).
PrioridadeOcorrencia = Prioridade

PRIORIDADE_PADRAO = PrioridadeOcorrencia.MEDIA

# Termos (sem acento, minúsculos) avaliados da maior para a menor prioridade; o primeiro que casar vence.
# Artigos do Código Penal entram como "art. 121" etc., do jeito que as tipificações são digitadas.
REGRAS_PRIORIDADE: tuple[tuple[PrioridadeOcorrencia, tuple[str, ...]], ...] = (
    (
        PrioridadeOcorrencia.URGENTE,
        (
            "homicidio", "feminicidio", "latrocinio", "estupro", "sequestro", "carcere privado",
            "tiroteio", "disparo de arma", "refem", "em andamento",
            "homicide", "murder", "kidnapping", "rape", "shooting", "hostage",
            "art. 121", "art. 148", "art. 159", "art. 213",
        ),
    ),
    (
        PrioridadeOcorrencia.ALTA,
        (
            "roubo", "lesao corporal", "violencia domestica", "maria da penha", "trafico", "porte ilegal",
            "arma de fogo", "acidente de transito com vitima", "com vitima",
            "robbery", "assault", "domestic violence", "drug trafficking", "firearm",
            "art. 129", "art. 157", "lei 11.340", "lei 11.343",
        ),
    ),
    (
        PrioridadeOcorrencia.BAIXA,
        (
            "perda", "extravio", "perturbacao do sossego", "sem vitima",
            "lost", "disturbance of the peace", "non-injury",
        ),
    ),
)


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sem_acento.lower().split())


def sugerir_prioridade(natureza: str, tipificacoes: Iterable[str] = ()) -> PrioridadeOcorrencia:
    """Prioridade sugerida pela natureza e pelas tipificações (artigo/descrição); sem regra → MEDIA."""
    texto = _normalizar(" | ".join([natureza, *tipificacoes]))
    for prioridade, termos in REGRAS_PRIORIDADE:
        if any(termo in texto for termo in termos):
            return prioridade
    return PRIORIDADE_PADRAO


def interpretar_prioridade(valor: str | None) -> PrioridadeOcorrencia | None:
    """Texto da borda → enum; vazio significa "deixar o sistema sugerir"."""
    if valor is None or not valor.strip():
        return None
    return interpretar_enum(
        PrioridadeOcorrencia, valor, "ocorrencia.prioridade_invalida", "Prioridade inválida: {valor}", normalizar=True
    )
