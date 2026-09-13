"""
Entidade Viatura + máquina de estados (RF15/RF16, ETAPA-04 §2).

DISPONIVEL ⇄ INDISPONIVEL (manual) · DISPONIVEL → EM_DESLOCAMENTO (despacho) →
OPERANDO → DISPONIVEL (liberação). Só DISPONIVEL pode ser despachada (UC02 regra 1).
Posição GPS é aceita apenas com timestamp dentro da janela de tolerância (RF16);
posição anterior é mantida se a nova for inválida (RNF04*).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4

from domain.shared.exceptions import CampoObrigatorioError, TransicaoInvalidaError, ValorInvalidoError
from domain.shared.geo import Coordenada


class SituacaoViatura(str, Enum):
    DISPONIVEL = "DISPONIVEL"
    EM_DESLOCAMENTO = "EM_DESLOCAMENTO"
    OPERANDO = "OPERANDO"
    INDISPONIVEL = "INDISPONIVEL"


@dataclass(frozen=True)
class Posicao:
    coordenada: Coordenada
    registrada_em: datetime

    def idade(self, agora: datetime) -> timedelta:
        return agora - self.registrada_em


@dataclass
class Viatura:
    prefixo: str
    placa: str
    id: UUID = field(default_factory=uuid4)
    situacao: SituacaoViatura = SituacaoViatura.DISPONIVEL
    ultima_posicao: Posicao | None = None
    versao: int = 1
    atualizada_em: datetime | None = None

    def __post_init__(self) -> None:
        if not self.prefixo or not self.prefixo.strip():
            raise CampoObrigatorioError("Prefixo da viatura é obrigatório.", chave="viatura.prefixo_vazio")
        if not self.placa or not self.placa.strip():
            raise CampoObrigatorioError("Placa da viatura é obrigatória.", chave="viatura.placa_vazia")
        self.prefixo = self.prefixo.strip().upper()
        self.placa = self.placa.strip().upper().replace(" ", "")

    # -------------------------------------------------------------- telemetria
    def registrar_posicao(self, coordenada: Coordenada, registrada_em: datetime, agora: datetime, tolerancia_segundos: int) -> None:
        if registrada_em.tzinfo is None:
            raise ValorInvalidoError("Timestamp da posição sem fuso horário.", chave="telemetria.timestamp_sem_fuso")
        desvio = abs((agora - registrada_em).total_seconds())
        if desvio > tolerancia_segundos:
            raise ValorInvalidoError(
                f"Timestamp da posição fora da janela de {tolerancia_segundos}s (desvio {desvio:.0f}s).",
                chave="telemetria.timestamp_fora_da_janela",
                desvio_segundos=int(desvio),
            )
        if self.ultima_posicao is not None and registrada_em < self.ultima_posicao.registrada_em:
            raise ValorInvalidoError("Posição mais antiga que a última registrada.", chave="telemetria.posicao_retroativa")
        self.ultima_posicao = Posicao(coordenada=coordenada, registrada_em=registrada_em)
        self.atualizada_em = agora

    def posicao_valida(self, agora: datetime, max_idade_segundos: int) -> bool:
        """RNF04*: posição com idade > limite não conta para sugestão automática."""
        return self.ultima_posicao is not None and self.ultima_posicao.idade(agora).total_seconds() <= max_idade_segundos

    def sinal(self, agora: datetime, max_idade_segundos: int) -> str:
        if self.ultima_posicao is None:
            return "SEM_POSICAO"
        return "OK" if self.posicao_valida(agora, max_idade_segundos) else "SEM_SINAL"

    # -------------------------------------------------------------- situação
    def _mudar(self, destino: SituacaoViatura, agora: datetime, permitidas: tuple[SituacaoViatura, ...]) -> None:
        if self.situacao not in permitidas:
            raise TransicaoInvalidaError(
                f"Viatura {self.prefixo} em {self.situacao.value} não pode ir para {destino.value}.",
                chave="viatura.transicao_invalida",
                situacao_atual=self.situacao.value,
                destino=destino.value,
            )
        self.situacao = destino
        self.versao += 1
        self.atualizada_em = agora

    def marcar_indisponivel(self, agora: datetime) -> None:
        """Manual, pelo Operador. Viatura despachada não pode ser retirada (RF15 aceite 2)."""
        self._mudar(SituacaoViatura.INDISPONIVEL, agora, (SituacaoViatura.DISPONIVEL,))

    def marcar_disponivel(self, agora: datetime) -> None:
        self._mudar(SituacaoViatura.DISPONIVEL, agora, (SituacaoViatura.INDISPONIVEL,))

    def despachar(self, agora: datetime) -> None:
        self._mudar(SituacaoViatura.EM_DESLOCAMENTO, agora, (SituacaoViatura.DISPONIVEL,))

    def chegar_ao_local(self, agora: datetime) -> None:
        self._mudar(SituacaoViatura.OPERANDO, agora, (SituacaoViatura.EM_DESLOCAMENTO,))

    def liberar(self, agora: datetime) -> None:
        """Fim do atendimento (RF19): volta a DISPONIVEL."""
        self._mudar(SituacaoViatura.DISPONIVEL, agora, (SituacaoViatura.EM_DESLOCAMENTO, SituacaoViatura.OPERANDO))

    @property
    def despachavel(self) -> bool:
        return self.situacao == SituacaoViatura.DISPONIVEL
