"""Eventos de auditoria das provas da ocorrência: evidências (RF01) e apreensões/custódia (RF03) · RNF03."""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Self
from uuid import UUID

from domain.auditoria.evento import EventoAuditoria
from domain.ocorrencia.apreensao import ItemApreendido, MovimentacaoCustodia
from domain.ocorrencia.entity import Evidencia


# ------------------------------------------------------------------- evidências
@dataclass(frozen=True, kw_only=True)
class EventoEvidencia(EventoAuditoria):
    ENTIDADE: ClassVar[str] = "Evidencia"

    evidencia_id: UUID
    ocorrencia_id: UUID

    def id_entidade(self) -> str | None:
        return str(self.evidencia_id)

    @abstractmethod
    def _detalhe(self) -> dict[str, Any]: ...

    def dados_depois(self) -> dict[str, Any] | None:
        return {"ocorrencia_id": str(self.ocorrencia_id), **self._detalhe()}


@dataclass(frozen=True, kw_only=True)
class EvidenciaAnexada(EventoEvidencia):
    OPERACAO: ClassVar[str] = "evidencia.anexar"

    nome_original: str
    formato: str
    tamanho: int
    hash_sha256: str

    @classmethod
    def de(cls, ocorrencia_id: UUID, evidencia: Evidencia) -> Self:
        return cls(
            evidencia_id=evidencia.id,
            ocorrencia_id=ocorrencia_id,
            nome_original=evidencia.nome_original,
            formato=evidencia.formato,
            tamanho=evidencia.tamanho,
            hash_sha256=evidencia.hash_sha256,
        )

    def _detalhe(self) -> dict[str, Any]:
        return {"nome_original": self.nome_original, "formato": self.formato, "tamanho": self.tamanho, "hash_sha256": self.hash_sha256}


@dataclass(frozen=True, kw_only=True)
class AcessoEvidencia(EventoEvidencia):
    """Leitura do arquivo da evidência, com o resultado da conferência de integridade."""

    integridade: str

    def _detalhe(self) -> dict[str, Any]:
        return {"integridade": self.integridade}


@dataclass(frozen=True, kw_only=True)
class EvidenciaBaixada(AcessoEvidencia):
    OPERACAO: ClassVar[str] = "evidencia.download"


@dataclass(frozen=True, kw_only=True)
class IntegridadeEvidenciaVerificada(AcessoEvidencia):
    OPERACAO: ClassVar[str] = "evidencia.verificar_integridade"


# --------------------------------------------------------- apreensões e custódia
@dataclass(frozen=True, kw_only=True)
class EventoItemApreendido(EventoAuditoria):
    ENTIDADE: ClassVar[str] = "ItemApreendido"

    item_id: UUID
    ocorrencia_id: UUID

    def id_entidade(self) -> str | None:
        return str(self.item_id)


@dataclass(frozen=True, kw_only=True)
class ItemApreendidoRegistrado(EventoItemApreendido):
    OPERACAO: ClassVar[str] = "apreensao.registrar"

    tipo: str
    numero_lacre: str
    quantidade: int
    unidade: str
    localizacao_deposito: str

    @classmethod
    def de(cls, ocorrencia_id: UUID, item: ItemApreendido) -> Self:
        return cls(
            item_id=item.id,
            ocorrencia_id=ocorrencia_id,
            tipo=item.tipo.value,
            numero_lacre=item.numero_lacre,
            quantidade=item.quantidade,
            unidade=item.unidade.value,
            localizacao_deposito=item.localizacao_deposito,
        )

    def dados_depois(self) -> dict[str, Any] | None:
        return {
            "ocorrencia_id": str(self.ocorrencia_id),
            "tipo": self.tipo,
            "numero_lacre": self.numero_lacre,
            "quantidade": self.quantidade,
            "unidade": self.unidade,
            "localizacao_deposito": self.localizacao_deposito,
        }


@dataclass(frozen=True, kw_only=True)
class CustodiaMovimentada(EventoItemApreendido):
    OPERACAO: ClassVar[str] = "apreensao.movimentar"

    origem: str | None
    destino: str
    observacao: str | None

    @classmethod
    def de(cls, ocorrencia_id: UUID, item_id: UUID, movimentacao: MovimentacaoCustodia) -> Self:
        return cls(
            item_id=item_id,
            ocorrencia_id=ocorrencia_id,
            origem=movimentacao.origem,
            destino=movimentacao.destino,
            observacao=movimentacao.observacao,
        )

    def dados_antes(self) -> dict[str, Any] | None:
        return {"localizacao": self.origem}

    def dados_depois(self) -> dict[str, Any] | None:
        return {"ocorrencia_id": str(self.ocorrencia_id), "localizacao": self.destino, "observacao": self.observacao}


@dataclass(frozen=True, kw_only=True)
class AutoApreensaoEmitido(EventoAuditoria):
    OPERACAO: ClassVar[str] = "apreensao.emitir_auto"
    ENTIDADE: ClassVar[str] = "AutoApreensao"

    numero: str
    ocorrencia_id: UUID
    itens: int
    hash_sha256: str

    def id_entidade(self) -> str | None:
        return self.numero

    def dados_depois(self) -> dict[str, Any] | None:
        return {"ocorrencia_id": str(self.ocorrencia_id), "itens": self.itens, "hash_sha256": self.hash_sha256}
