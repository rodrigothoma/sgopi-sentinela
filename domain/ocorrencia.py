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


class StatusOcorrencia(str, Enum):
    """
    Máquina de estados da ocorrência.

    Vocabulário alinhado à seção 3.2 e ao UC01/UC02/UC04 da Documentação de
    Engenharia — é o nome oficial usado por código, testes e telas.

    `Rascunho` (formulário ainda não submetido) não é um status persistido:
    conforme o UC01, a ocorrência só é gravada no banco no momento da
    submissão, já com o status inicial AGUARDANDO_REVISAO.

    O estado `Em Correção` aparece no cenário alternativo do UC04, mas não
    faz parte da máquina de estados do MVP (seção 3.2) nem das tarefas de
    Sprint 2/3 do Planejamento de Desenvolvimento — por isso não está
    listado aqui; fica em aberto para decisão futura da equipe.
    """
    AGUARDANDO_REVISAO = "AGUARDANDO_REVISAO"
    VALIDADA = "VALIDADA"
    REJEITADA = "REJEITADA"


class TransicaoInvalidaError(Exception):
    """Levantada quando uma transição de estado não é permitida."""


@dataclass
class Ocorrencia:
    agente_policial_id: UUID
    descricao: str
    localizacao: str
    id: UUID = field(default_factory=uuid4)
    numero_protocolo: str | None = None
    status: StatusOcorrencia = StatusOcorrencia.AGUARDANDO_REVISAO
    criada_em: datetime = field(default_factory=lambda: datetime.now(UTC))
    validada_por_id: UUID | None = None

    def __post_init__(self) -> None:
        if not self.descricao or not self.descricao.strip():
            raise ValueError("A descrição da ocorrência não pode ser vazia.")
        if not self.localizacao or not self.localizacao.strip():
            raise ValueError("A localização da ocorrência é obrigatória.")
        if self.numero_protocolo is None:
            self.numero_protocolo = self._gerar_numero_protocolo()

    def _gerar_numero_protocolo(self) -> str:
        ano = self.criada_em.year
        sufixo = str(self.id).split("-")[0].upper()
        return f"SGOPI-{ano}-{sufixo}"

    def validar(self, delegado_id: UUID) -> None:
        if self.status != StatusOcorrencia.AGUARDANDO_REVISAO:
            raise TransicaoInvalidaError(
                f"Só é possível validar a partir de AGUARDANDO_REVISAO "
                f"(status atual: {self.status})."
            )
        self.status = StatusOcorrencia.VALIDADA
        self.validada_por_id = delegado_id

    def rejeitar(self, delegado_id: UUID) -> None:
        if self.status != StatusOcorrencia.AGUARDANDO_REVISAO:
            raise TransicaoInvalidaError(
                f"Só é possível rejeitar a partir de AGUARDANDO_REVISAO "
                f"(status atual: {self.status})."
            )
        self.status = StatusOcorrencia.REJEITADA
        self.validada_por_id = delegado_id
