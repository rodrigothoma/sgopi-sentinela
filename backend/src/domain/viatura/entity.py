"""
Entidade Viatura + máquina de estados (RF02, ETAPA-04 §2).

DISPONIVEL ⇄ INDISPONIVEL (manual) · DISPONIVEL → EM_DESLOCAMENTO (despacho) →
OPERANDO → DISPONIVEL (liberação). Só DISPONIVEL pode ser despachada (UC02 regra 1).
Posição GPS é aceita apenas com timestamp dentro da janela de tolerância (RF02);
posição anterior é mantida se a nova for inválida (RNF04*).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4

from domain.shared.exceptions import TransicaoInvalidaError, ValorInvalidoError
from domain.shared.geo import Coordenada
from domain.shared.maquina_estados import MaquinaEstados
from domain.shared.validacao import exigir_texto
from domain.shared.versionado import Versionado


class SituacaoViatura(str, Enum):
    DISPONIVEL = "DISPONIVEL"
    EM_DESLOCAMENTO = "EM_DESLOCAMENTO"
    OPERANDO = "OPERANDO"
    INDISPONIVEL = "INDISPONIVEL"


class OperacaoViatura(str, Enum):
    MARCAR_INDISPONIVEL = "marcar_indisponivel"
    MARCAR_DISPONIVEL = "marcar_disponivel"
    DESPACHAR = "despachar"
    CHEGAR_AO_LOCAL = "chegar_ao_local"
    LIBERAR = "liberar"


_D, _I, _E, _O = (
    SituacaoViatura.DISPONIVEL,
    SituacaoViatura.INDISPONIVEL,
    SituacaoViatura.EM_DESLOCAMENTO,
    SituacaoViatura.OPERANDO,
)
MAQUINA_VIATURA: MaquinaEstados[SituacaoViatura, OperacaoViatura] = MaquinaEstados(
    {
        (_D, OperacaoViatura.MARCAR_INDISPONIVEL): _I,  # manual; despachada não pode ser retirada (RF02 aceite 2)
        (_I, OperacaoViatura.MARCAR_DISPONIVEL): _D,
        (_D, OperacaoViatura.DESPACHAR): _E,
        (_E, OperacaoViatura.CHEGAR_AO_LOCAL): _O,
        (_E, OperacaoViatura.LIBERAR): _D,  # fim do atendimento (RF02)
        (_O, OperacaoViatura.LIBERAR): _D,
    }
)


@dataclass(frozen=True)
class Posicao:
    coordenada: Coordenada
    registrada_em: datetime

    def idade(self, agora: datetime) -> timedelta:
        return agora - self.registrada_em


@dataclass
class Viatura(Versionado):
    prefixo: str
    placa: str
    id: UUID = field(default_factory=uuid4)
    situacao: SituacaoViatura = SituacaoViatura.DISPONIVEL
    ultima_posicao: Posicao | None = None
    versao: int = 1
    atualizada_em: datetime | None = None

    def __post_init__(self) -> None:
        exigir_texto(self.prefixo, "Prefixo da viatura é obrigatório.", chave="viatura.prefixo_vazio")
        exigir_texto(self.placa, "Placa da viatura é obrigatória.", chave="viatura.placa_vazia")
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
    def _mudar(self, operacao: OperacaoViatura, agora: datetime) -> None:
        destino = MAQUINA_VIATURA.proximo(self.situacao, operacao)
        if destino is None:
            (alvo,) = MAQUINA_VIATURA.destinos(operacao)
            raise TransicaoInvalidaError(
                f"Viatura {self.prefixo} em {self.situacao.value} não pode ir para {alvo.value}.",
                chave="viatura.transicao_invalida",
                situacao_atual=self.situacao.value,
                destino=alvo.value,
            )
        self.situacao = destino
        self._tocar(agora)

    def marcar_indisponivel(self, agora: datetime) -> None:
        """Manual, pelo Operador. Viatura despachada não pode ser retirada (RF02 aceite 2)."""
        self._mudar(OperacaoViatura.MARCAR_INDISPONIVEL, agora)

    def marcar_disponivel(self, agora: datetime) -> None:
        self._mudar(OperacaoViatura.MARCAR_DISPONIVEL, agora)

    def despachar(self, agora: datetime) -> None:
        self._mudar(OperacaoViatura.DESPACHAR, agora)

    def chegar_ao_local(self, agora: datetime) -> None:
        self._mudar(OperacaoViatura.CHEGAR_AO_LOCAL, agora)

    def liberar(self, agora: datetime) -> None:
        """Fim do atendimento (RF02): volta a DISPONIVEL."""
        self._mudar(OperacaoViatura.LIBERAR, agora)

    @property
    def despachavel(self) -> bool:
        return self.situacao == SituacaoViatura.DISPONIVEL
