"""
Entidade de domínio: Inquerito Policial (RF06 / UC06).

Regra de ouro: não importa frameworks nem camadas externas (RNF05).
Agrupa múltiplas ocorrências policiais validadas sob um mesmo procedimento formal,
instaurado e gerido pelo Delegado de Polícia.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from domain.shared.exceptions import CampoObrigatorioError, ConflitoError, ValorInvalidoError

TAMANHO_MINIMO_EMENTA = 10


class StatusInquerito(str, Enum):
    """Ciclo de vida de um Inquérito Policial (IP)."""

    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDO = "CONCLUIDO"
    ARQUIVADO = "ARQUIVADO"


@dataclass
class Inquerito:
    """Procedimento policial formal que consolida múltiplas ocorrências e laudos."""

    numero: str  # Padrão: IP-AAAA-NNNNNN
    ementa: str
    delegado_id: UUID
    data_abertura: datetime
    id: UUID = field(default_factory=uuid4)
    status: StatusInquerito = StatusInquerito.EM_ANDAMENTO
    relatorio_final: str | None = None
    motivo_arquivamento: str | None = None
    concluido_em: datetime | None = None
    atualizado_em: datetime | None = None
    ocorrencias_ids: list[UUID] = field(default_factory=list)
    ativo: bool = True
    versao: int = 1

    def __post_init__(self) -> None:
        if self.atualizado_em is None:
            self.atualizado_em = self.data_abertura

    @classmethod
    def instaurar(
        cls,
        *,
        numero: str,
        ementa: str,
        delegado_id: UUID,
        instante: datetime,
        ocorrencias_iniciais_ids: list[UUID] | None = None,
    ) -> Inquerito:
        ementa_limpa = ementa.strip() if ementa else ""
        if len(ementa_limpa) < TAMANHO_MINIMO_EMENTA:
            raise CampoObrigatorioError(
                f"A ementa do inquérito deve conter no mínimo {TAMANHO_MINIMO_EMENTA} caracteres.",
                chave="inquerito.ementa_curta",
            )
        if not numero or not numero.strip():
            raise CampoObrigatorioError("Número do inquérito é obrigatório.", chave="inquerito.numero_obrigatorio")

        return cls(
            numero=numero.strip(),
            ementa=ementa_limpa,
            delegado_id=delegado_id,
            data_abertura=instante,
            atualizado_em=instante,
            ocorrencias_ids=list(ocorrencias_iniciais_ids or []),
        )

    def vincular_ocorrencia(self, ocorrencia_id: UUID, instante: datetime) -> None:
        if self.status != StatusInquerito.EM_ANDAMENTO:
            raise ConflitoError(
                f"Não é permitido vincular ocorrências a inquérito {self.status.value}.",
                chave="inquerito.status_invalido_vinculacao",
            )
        if ocorrencia_id in self.ocorrencias_ids:
            return
        self.ocorrencias_ids.append(ocorrencia_id)
        self.atualizado_em = instante
        self.versao += 1

    def desvincular_ocorrencia(self, ocorrencia_id: UUID, instante: datetime) -> None:
        if self.status != StatusInquerito.EM_ANDAMENTO:
            raise ConflitoError(
                f"Não é permitido alterar ocorrências de inquérito {self.status.value}.",
                chave="inquerito.status_invalido_alteracao",
            )
        if ocorrencia_id in self.ocorrencias_ids:
            self.ocorrencias_ids.remove(ocorrencia_id)
            self.atualizado_em = instante
            self.versao += 1

    def concluir(self, relatorio_final: str, instante: datetime) -> None:
        if self.status != StatusInquerito.EM_ANDAMENTO:
            raise ConflitoError(
                f"Apenas inquéritos em andamento podem ser concluídos (status: {self.status.value}).",
                chave="inquerito.ja_finalizado",
            )
        relatorio = relatorio_final.strip() if relatorio_final else ""
        if len(relatorio) < TAMANHO_MINIMO_EMENTA:
            raise ValorInvalidoError(
                "O relatório final de conclusão deve conter no mínimo 10 caracteres.",
                chave="inquerito.relatorio_curto",
            )
        self.status = StatusInquerito.CONCLUIDO
        self.relatorio_final = relatorio
        self.concluido_em = instante
        self.atualizado_em = instante
        self.versao += 1

    def arquivar(self, motivo: str, instante: datetime) -> None:
        if self.status != StatusInquerito.EM_ANDAMENTO:
            raise ConflitoError(
                f"Apenas inquéritos em andamento podem ser arquivados (status: {self.status.value}).",
                chave="inquerito.ja_finalizado",
            )
        motivo_limpo = motivo.strip() if motivo else ""
        if len(motivo_limpo) < TAMANHO_MINIMO_EMENTA:
            raise ValorInvalidoError(
                "O motivo do arquivamento deve conter no mínimo 10 caracteres.",
                chave="inquerito.motivo_curto",
            )
        self.status = StatusInquerito.ARQUIVADO
        self.motivo_arquivamento = motivo_limpo
        self.concluido_em = instante
        self.atualizado_em = instante
        self.versao += 1
