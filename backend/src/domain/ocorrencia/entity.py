"""
Entidade de domínio: Ocorrencia

Regra de ouro do domínio: nenhuma linha aqui pode importar FastAPI,
SQLAlchemy ou qualquer outra biblioteca externa (RNF05). Esta classe
representa apenas a regra de negócio pura de uma ocorrência policial.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from domain.shared.exceptions import TransicaoInvalidaError  # noqa: F401 — re-exportado para compatibilidade


class StatusOcorrencia(str, Enum):
    """Máquina de estados da ocorrência (fluxo descrito no MVP do README)."""
    REGISTRADA = "REGISTRADA"
    EM_VALIDACAO = "EM_VALIDACAO"
    VALIDADA = "VALIDADA"
    REJEITADA = "REJEITADA"


class TipoEnvolvido(str, Enum):
    """Papel do envolvido na ocorrência policial."""
    VITIMA = "VITIMA"
    TESTEMUNHA = "TESTEMUNHA"
    SUSPEITO = "SUSPEITO"


@dataclass
class Envolvido:
    """Pessoa relacionada à ocorrência (vítima, testemunha ou suspeito)."""
    nome: str
    tipo: TipoEnvolvido
    id: UUID = field(default_factory=uuid4)
    documento: str | None = None


@dataclass
class TipificacaoPenal:
    """Enquadramento legal aplicável à ocorrência."""
    artigo: str
    descricao: str


@dataclass
class Ocorrencia:
    """Entidade principal — representa uma ocorrência policial registrada."""
    agente_policial_id: UUID
    natureza: str
    descricao: str
    localizacao: str
    id: UUID = field(default_factory=uuid4)
    numero_protocolo: str | None = None
    status: StatusOcorrencia = StatusOcorrencia.REGISTRADA
    criada_em: datetime = field(default_factory=lambda: datetime.now(UTC))
    validada_por_id: UUID | None = None
    tipificacoes: list[TipificacaoPenal] = field(default_factory=list)
    envolvidos: list[Envolvido] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.descricao or not self.descricao.strip():
            raise ValueError("A descrição da ocorrência não pode ser vazia.")
        if not self.localizacao or not self.localizacao.strip():
            raise ValueError("A localização da ocorrência é obrigatória.")
        if self.numero_protocolo is None:
            self.numero_protocolo = self._gerar_numero_protocolo()

    def _gerar_numero_protocolo(self) -> str:
        """Gera o número de protocolo único no formato SGOPI-{ano}-{prefixo_uuid}."""
        ano = self.criada_em.year
        sufixo = str(self.id).split("-")[0].upper()
        return f"SGOPI-{ano}-{sufixo}"

    def enviar_para_validacao(self) -> None:
        """Transiciona de REGISTRADA para EM_VALIDACAO."""
        if self.status != StatusOcorrencia.REGISTRADA:
            raise TransicaoInvalidaError(
                f"Só é possível enviar para validação a partir de REGISTRADA "
                f"(status atual: {self.status})."
            )
        self.status = StatusOcorrencia.EM_VALIDACAO

    def validar(self, delegado_id: UUID) -> None:
        """Transiciona de EM_VALIDACAO para VALIDADA, registrando o delegado."""
        if self.status != StatusOcorrencia.EM_VALIDACAO:
            raise TransicaoInvalidaError(
                f"Só é possível validar a partir de EM_VALIDACAO "
                f"(status atual: {self.status})."
            )
        self.status = StatusOcorrencia.VALIDADA
        self.validada_por_id = delegado_id

    def rejeitar(self, delegado_id: UUID) -> None:
        """Transiciona de EM_VALIDACAO para REJEITADA, registrando o delegado."""
        if self.status != StatusOcorrencia.EM_VALIDACAO:
            raise TransicaoInvalidaError(
                f"Só é possível rejeitar a partir de EM_VALIDACAO "
                f"(status atual: {self.status})."
            )
        self.status = StatusOcorrencia.REJEITADA
        self.validada_por_id = delegado_id

    def adicionar_envolvido(self, envolvido: Envolvido) -> None:
        """Adiciona um envolvido à ocorrência, proibindo duplicidade por ID."""
        ids_existentes = {e.id for e in self.envolvidos}
        if envolvido.id in ids_existentes:
            raise ValueError(
                f"Envolvido com id {envolvido.id} já foi adicionado a esta ocorrência."
            )
        self.envolvidos.append(envolvido)
