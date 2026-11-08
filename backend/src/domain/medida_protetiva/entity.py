"""
Entidade de domínio: Medida Protetiva de Urgência (RF09 / UC09).

Regra de ouro: não importa frameworks nem camadas externas (RNF05).
Trata da formalização, controle estrito de vigência, restrições judiciais/policiais
e prorrogações auditadas para proteção de vítimas qualificadas em ocorrências (RNF03).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4

from domain.shared.exceptions import CampoObrigatorioError, ConflitoError, ValorInvalidoError
from domain.shared.maquina_estados import MaquinaEstados
from domain.shared.validacao import exigir_texto
from domain.shared.versionado import Versionado

TAMANHO_MINIMO_JUSTIFICATIVA = 10
TAMANHO_MINIMO_MOTIVO = 10


class StatusMedida(str, Enum):
    """Situação jurídica da medida protetiva."""

    ATIVA = "ATIVA"
    RENOVADA = "RENOVADA"
    REVOGADA = "REVOGADA"
    EXPIRADA = "EXPIRADA"


# Medida em vigor: pode ser renovada, revogada e gera alerta de vencimento.
ESTADOS_VIGENTES = frozenset({StatusMedida.ATIVA, StatusMedida.RENOVADA})


class OperacaoMedida(str, Enum):
    RENOVAR = "renovar"
    REVOGAR = "revogar"


MAQUINA_MEDIDA: MaquinaEstados[StatusMedida, OperacaoMedida] = MaquinaEstados(
    {(origem, OperacaoMedida.RENOVAR): StatusMedida.RENOVADA for origem in ESTADOS_VIGENTES}
    | {(origem, OperacaoMedida.REVOGAR): StatusMedida.REVOGADA for origem in ESTADOS_VIGENTES}
)


class TipoRestricao(str, Enum):
    """Tipos legais de restrição impostos ao agressor."""

    AFASTAMENTO_DO_LAR = "AFASTAMENTO_DO_LAR"
    PROIBICAO_DE_CONTATO = "PROIBICAO_DE_CONTATO"
    LIMITE_DISTANCIA_METROS = "LIMITE_DISTANCIA_METROS"
    SUSPENSAO_PORTE_ARMAS = "SUSPENSAO_PORTE_ARMAS"
    OUTRA = "OUTRA"


@dataclass
class MedidaProtetiva(Versionado):
    """Medida restritiva protetiva com prazo temporal e vigilância ativa."""

    numero_referencia: str  # Padrão: MP-AAAA-NNNNNN
    ocorrencia_id: UUID
    delegado_id: UUID
    vitima_id: UUID
    agressor_id: UUID
    tipos_restricao: list[str]
    data_inicio: date
    prazo_dias: int
    data_vencimento: date
    criada_em: datetime  # instante do Relogio do caso de uso: o domínio não lê o relógio
    id: UUID = field(default_factory=uuid4)
    distancia_minima_metros: int | None = None
    condicoes_especificas: str | None = None
    motivo_revogacao: str | None = None
    justificativa_renovacao: str | None = None
    status: StatusMedida = StatusMedida.ATIVA
    atualizada_em: datetime | None = None
    ativo: bool = True
    versao: int = 1
    alerta_vencimento_enviado_em: datetime | None = None

    def __post_init__(self) -> None:
        if self.atualizada_em is None:
            self.atualizada_em = self.criada_em

    @classmethod
    def conceder(
        cls,
        *,
        numero_referencia: str,
        ocorrencia_id: UUID,
        delegado_id: UUID,
        vitima_id: UUID,
        agressor_id: UUID,
        tipos_restricao: list[str],
        data_inicio: date,
        prazo_dias: int,
        instante: datetime,
        distancia_minima_metros: int | None = None,
        condicoes_especificas: str | None = None,
    ) -> MedidaProtetiva:
        if vitima_id == agressor_id:
            raise ValorInvalidoError(
                "A vítima e o agressor não podem ser a mesma pessoa.",
                chave="medida.vitima_e_agressor_iguais",
            )
        if not tipos_restricao:
            raise CampoObrigatorioError(
                "Informe ao menos um tipo de restrição para a medida protetiva.",
                chave="medida.restricao_obrigatoria",
            )
        if prazo_dias < 1 or prazo_dias > 730:
            raise ValorInvalidoError(
                "O prazo da medida protetiva deve ser entre 1 e 730 dias (2 anos).",
                chave="medida.prazo_invalido",
            )
        data_venc = data_inicio + timedelta(days=prazo_dias)

        return cls(
            numero_referencia=numero_referencia.strip(),
            ocorrencia_id=ocorrencia_id,
            delegado_id=delegado_id,
            vitima_id=vitima_id,
            agressor_id=agressor_id,
            tipos_restricao=list(tipos_restricao),
            data_inicio=data_inicio,
            prazo_dias=prazo_dias,
            data_vencimento=data_venc,
            distancia_minima_metros=distancia_minima_metros,
            condicoes_especificas=condicoes_especificas.strip() if condicoes_especificas else None,
            criada_em=instante,
            atualizada_em=instante,
        )

    def renovar(self, dias_adicionais: int, justificativa: str, instante: datetime) -> None:
        destino = MAQUINA_MEDIDA.proximo(self.status, OperacaoMedida.RENOVAR)
        if destino is None:
            raise ConflitoError(
                f"Apenas medidas ativas podem ser renovadas (status: {self.status.value}).",
                chave="medida.status_invalido_renovacao",
            )
        if dias_adicionais < 1 or dias_adicionais > 365:
            raise ValorInvalidoError(
                "O prazo adicional de prorrogação deve ser entre 1 e 365 dias.",
                chave="medida.prazo_adicional_invalido",
            )
        just = exigir_texto(justificativa, f"A justificativa técnica para prorrogação deve ter no mínimo {TAMANHO_MINIMO_JUSTIFICATIVA} caracteres.", chave="medida.justificativa_curta", minimo=TAMANHO_MINIMO_JUSTIFICATIVA)

        self.prazo_dias += dias_adicionais
        self.data_vencimento = self.data_vencimento + timedelta(days=dias_adicionais)
        self.justificativa_renovacao = just
        self.status = destino
        self._tocar(instante)

    def revogar(self, motivo: str, instante: datetime) -> None:
        destino = MAQUINA_MEDIDA.proximo(self.status, OperacaoMedida.REVOGAR)
        if destino is None:
            raise ConflitoError(
                f"Apenas medidas ativas podem ser revogadas (status: {self.status.value}).",
                chave="medida.status_invalido_revogacao",
            )
        motivo_limpo = exigir_texto(motivo, f"O motivo da revogação deve ter no mínimo {TAMANHO_MINIMO_MOTIVO} caracteres.", chave="medida.motivo_curto", minimo=TAMANHO_MINIMO_MOTIVO)
        self.status = destino
        self.motivo_revogacao = motivo_limpo
        self._tocar(instante)

    def dias_restantes(self, hoje: date) -> int:
        return (self.data_vencimento - hoje).days

    def esta_proxima_do_vencimento(self, hoje: date, dias_antecedencia: int = 3) -> bool:
        """Indica se a medida está ativa e vence em até N dias (72h por padrão - UC12) ou já venceu."""
        if self.status not in ESTADOS_VIGENTES:
            return False
        return self.dias_restantes(hoje) <= dias_antecedencia

    def marcar_alerta_vencimento_enviado(self, instante: datetime) -> None:
        self.alerta_vencimento_enviado_em = instante
        self.atualizada_em = instante

