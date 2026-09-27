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


class StatusMedida(str, Enum):
    """Situação jurídica da medida protetiva."""

    ATIVA = "ATIVA"
    RENOVADA = "RENOVADA"
    REVOGADA = "REVOGADA"
    EXPIRADA = "EXPIRADA"


class TipoRestricao(str, Enum):
    """Tipos legais de restrição impostos ao agressor."""

    AFASTAMENTO_DO_LAR = "AFASTAMENTO_DO_LAR"
    PROIBICAO_DE_CONTATO = "PROIBICAO_DE_CONTATO"
    LIMITE_DISTANCIA_METROS = "LIMITE_DISTANCIA_METROS"
    SUSPENSAO_PORTE_ARMAS = "SUSPENSAO_PORTE_ARMAS"
    OUTRA = "OUTRA"


@dataclass
class MedidaProtetiva:
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
    id: UUID = field(default_factory=uuid4)
    distancia_minima_metros: int | None = None
    condicoes_especificas: str | None = None
    motivo_revogacao: str | None = None
    justificativa_renovacao: str | None = None
    status: StatusMedida = StatusMedida.ATIVA
    criada_em: datetime = field(default_factory=lambda: datetime.now())
    atualizada_em: datetime | None = None
    ativo: bool = True
    versao: int = 1

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
        if self.status not in (StatusMedida.ATIVA, StatusMedida.RENOVADA):
            raise ConflitoError(
                f"Apenas medidas ativas podem ser renovadas (status: {self.status.value}).",
                chave="medida.status_invalido_renovacao",
            )
        if dias_adicionais < 1 or dias_adicionais > 365:
            raise ValorInvalidoError(
                "O prazo adicional de prorrogação deve ser entre 1 e 365 dias.",
                chave="medida.prazo_adicional_invalido",
            )
        just = justificativa.strip() if justificativa else ""
        if len(just) < 10:
            raise CampoObrigatorioError(
                "A justificativa técnica para prorrogação deve ter no mínimo 10 caracteres.",
                chave="medida.justificativa_curta",
            )

        self.prazo_dias += dias_adicionais
        self.data_vencimento = self.data_vencimento + timedelta(days=dias_adicionais)
        self.justificativa_renovacao = just
        self.status = StatusMedida.RENOVADA
        self.atualizada_em = instante
        self.versao += 1

    def revogar(self, motivo: str, instante: datetime) -> None:
        if self.status not in (StatusMedida.ATIVA, StatusMedida.RENOVADA):
            raise ConflitoError(
                f"Apenas medidas ativas podem ser revogadas (status: {self.status.value}).",
                chave="medida.status_invalido_revogacao",
            )
        motivo_limpo = motivo.strip() if motivo else ""
        if len(motivo_limpo) < 10:
            raise CampoObrigatorioError(
                "O motivo da revogação deve ter no mínimo 10 caracteres.",
                chave="medida.motivo_curto",
            )
        self.status = StatusMedida.REVOGADA
        self.motivo_revogacao = motivo_limpo
        self.atualizada_em = instante
        self.versao += 1

    def dias_restantes(self, hoje: date) -> int:
        return (self.data_vencimento - hoje).days
