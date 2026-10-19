"""
Porta de saída: ConsultaIndicadores (sugestão #11). Agregações somente leitura sobre ocorrências,
histórico de status, ordens de despacho e viaturas — calculadas no banco (GROUP BY/AVG), nunca em
Python sobre uma página limitada. Os períodos são intervalos fechados ``[de, ate]`` em UTC.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MediaDuracao:
    segundos: float | None  # None quando não há amostras no período
    amostras: int


class ConsultaIndicadores(ABC):
    @abstractmethod
    async def ocorrencias_por_natureza(self, de: datetime, ate: datetime) -> dict[str, int]:
        """Ocorrências criadas no período (exceto excluídas) por natureza."""

    @abstractmethod
    async def ocorrencias_por_origem(self, de: datetime, ate: datetime) -> dict[str, int]: ...

    @abstractmethod
    async def ocorrencias_por_hora_utc(self, de: datetime, ate: datetime) -> dict[int, int]:
        """Hora UTC (0–23) do fato → quantidade, para ocorrências criadas no período."""

    @abstractmethod
    async def decisoes_do_delegado(self, de: datetime, ate: datetime) -> dict[str, int]:
        """Saídas de AGUARDANDO_REVISAO no período por destino (VALIDADA, EM_CORRECAO, REJEITADA)."""

    @abstractmethod
    async def tempo_ate_primeira_decisao(self, de: datetime, ate: datetime) -> MediaDuracao:
        """Da criação da ocorrência até a primeira decisão do Delegado (decisão dentro do período)."""

    @abstractmethod
    async def tempo_validacao_ate_despacho(self, de: datetime, ate: datetime) -> MediaDuracao:
        """Da validação até a primeira ordem de despacho (despacho dentro do período)."""

    @abstractmethod
    async def tempo_despacho_ate_encerramento(self, de: datetime, ate: datetime) -> MediaDuracao:
        """Da primeira ordem de despacho até o encerramento (encerramento dentro do período)."""

    @abstractmethod
    async def despachos_por_hora_utc(self, de: datetime, ate: datetime) -> dict[int, int]: ...

    @abstractmethod
    async def viaturas_por_situacao(self) -> dict[str, int]:
        """Retrato atual da frota (a situação não tem série histórica gravada)."""
