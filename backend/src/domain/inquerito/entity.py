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
from typing import ClassVar
from uuid import UUID, uuid4

from domain.shared.exceptions import CampoObrigatorioError, ConflitoError, ValorInvalidoError
from domain.shared.maquina_estados import MaquinaEstados
from domain.shared.versionado import Versionado

TAMANHO_MINIMO_EMENTA = 10


class StatusInquerito(str, Enum):
    """Ciclo de vida de um Inquérito Policial (IP)."""

    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDO = "CONCLUIDO"
    ARQUIVADO = "ARQUIVADO"


class OperacaoInquerito(str, Enum):
    VINCULAR_OCORRENCIA = "vincular_ocorrencia"
    DESVINCULAR_OCORRENCIA = "desvincular_ocorrencia"
    CONCLUIR = "concluir"
    ARQUIVAR = "arquivar"


# Só o inquérito EM_ANDAMENTO aceita alterações; vincular/desvincular são laços no mesmo estado.
MAQUINA_INQUERITO: MaquinaEstados[StatusInquerito, OperacaoInquerito] = MaquinaEstados(
    {
        (StatusInquerito.EM_ANDAMENTO, OperacaoInquerito.VINCULAR_OCORRENCIA): StatusInquerito.EM_ANDAMENTO,
        (StatusInquerito.EM_ANDAMENTO, OperacaoInquerito.DESVINCULAR_OCORRENCIA): StatusInquerito.EM_ANDAMENTO,
        (StatusInquerito.EM_ANDAMENTO, OperacaoInquerito.CONCLUIR): StatusInquerito.CONCLUIDO,
        (StatusInquerito.EM_ANDAMENTO, OperacaoInquerito.ARQUIVAR): StatusInquerito.ARQUIVADO,
    }
)


@dataclass
class Inquerito(Versionado):
    """Procedimento policial formal que consolida múltiplas ocorrências e laudos."""

    CAMPO_ATUALIZACAO: ClassVar[str] = "atualizado_em"

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
        if not MAQUINA_INQUERITO.permite(self.status, OperacaoInquerito.VINCULAR_OCORRENCIA):
            raise ConflitoError(
                f"Não é permitido vincular ocorrências a inquérito {self.status.value}.",
                chave="inquerito.status_invalido_vinculacao",
            )
        if ocorrencia_id in self.ocorrencias_ids:
            return
        self.ocorrencias_ids.append(ocorrencia_id)
        self._tocar(instante)

    def desvincular_ocorrencia(self, ocorrencia_id: UUID, instante: datetime) -> None:
        if not MAQUINA_INQUERITO.permite(self.status, OperacaoInquerito.DESVINCULAR_OCORRENCIA):
            raise ConflitoError(
                f"Não é permitido alterar ocorrências de inquérito {self.status.value}.",
                chave="inquerito.status_invalido_alteracao",
            )
        if ocorrencia_id in self.ocorrencias_ids:
            self.ocorrencias_ids.remove(ocorrencia_id)
            self._tocar(instante)

    def concluir(self, relatorio_final: str, instante: datetime) -> None:
        destino = MAQUINA_INQUERITO.proximo(self.status, OperacaoInquerito.CONCLUIR)
        if destino is None:
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
        self.status = destino
        self.relatorio_final = relatorio
        self.concluido_em = instante
        self._tocar(instante)

    def arquivar(self, motivo: str, instante: datetime) -> None:
        destino = MAQUINA_INQUERITO.proximo(self.status, OperacaoInquerito.ARQUIVAR)
        if destino is None:
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
        self.status = destino
        self.motivo_arquivamento = motivo_limpo
        self.concluido_em = instante
        self._tocar(instante)
