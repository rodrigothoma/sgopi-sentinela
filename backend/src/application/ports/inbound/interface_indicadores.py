"""Porta de entrada: painel de indicadores operacionais (sugestão #11 — RF01/RF02/RF04)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from application.ports.inbound.ator import Ator

FUSO_PADRAO = "America/Sao_Paulo"


@dataclass(frozen=True)
class IndicadoresInput:
    de: datetime | None = None  # ausente → ``ate`` menos o período padrão
    ate: datetime | None = None  # ausente → agora
    fuso: str = FUSO_PADRAO  # IANA; usado só para as faixas horárias


@dataclass(frozen=True)
class ContagemOutput:
    chave: str
    total: int


@dataclass(frozen=True)
class DuracaoOutput:
    media_segundos: float | None
    amostras: int


@dataclass(frozen=True)
class IndicadoresOutput:
    de: str
    ate: str
    fuso: str
    total_ocorrencias: int
    por_natureza: tuple[ContagemOutput, ...]
    por_origem: tuple[ContagemOutput, ...]
    por_faixa_horaria: tuple[int, ...]  # 24 posições, hora local do fato
    decisoes: tuple[ContagemOutput, ...]  # VALIDADA | EM_CORRECAO | REJEITADA
    taxa_devolucao: float | None  # 0–1 sobre o total de decisões
    taxa_rejeicao: float | None
    tempo_ate_decisao: DuracaoOutput
    tempo_validacao_despacho: DuracaoOutput
    tempo_despacho_encerramento: DuracaoOutput
    despachos_por_hora: tuple[int, ...]  # 24 posições, hora local
    viaturas_por_situacao: tuple[ContagemOutput, ...]


class InterfaceCalcularIndicadores(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: IndicadoresInput) -> IndicadoresOutput: ...
