"""
Eventos de auditoria do ciclo de vida da ocorrência (RF01/RF04/RF02 · RNF03).

Hierarquia:
- ``EventoOcorrencia`` (abstrata): entidade ``Ocorrencia`` e o id do registro afetado;
- ``MudancaStatusOcorrencia`` (abstrata): o par status/versão antes e depois, comum a
  reenvio, decisões do Delegado e encerramento;
- ``DecisaoSobreOcorrencia`` (abstrata): decisões que registram um texto (despacho,
  justificativa ou motivo);
- uma classe concreta por ação, que só declara o nome da operação e o que for próprio dela.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, ClassVar, Self
from uuid import UUID

from domain.auditoria.evento import EventoAuditoria
from domain.ocorrencia.autenticidade import CodigoVerificacao, SituacaoDocumento
from domain.ocorrencia.entity import Ocorrencia
from domain.ocorrencia.prioridade import PrioridadeOcorrencia


@dataclass(frozen=True)
class SituacaoOcorrencia:
    """Fotografia de status e versão, tirada antes de alterar a ocorrência."""

    status: str
    versao: int

    @classmethod
    def de(cls, ocorrencia: Ocorrencia) -> SituacaoOcorrencia:
        return cls(status=ocorrencia.status.value, versao=ocorrencia.versao)

    def como_dict(self) -> dict[str, Any]:
        return {"status": self.status, "versao": self.versao}


@dataclass(frozen=True, kw_only=True)
class EventoOcorrencia(EventoAuditoria):
    ENTIDADE: ClassVar[str] = "Ocorrencia"
    ENTIDADE_GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ("ocorrencias",)

    ocorrencia_id: UUID

    def id_entidade(self) -> str | None:
        return str(self.ocorrencia_id)


@dataclass(frozen=True, kw_only=True)
class OcorrenciaRegistrada(EventoOcorrencia):
    OPERACAO: ClassVar[str] = "ocorrencia.registrar"

    status: str
    protocolo: str
    origem: str
    prioridade: str
    prioridade_sugerida: bool
    itens_apreendidos: int

    @classmethod
    def de(cls, ocorrencia: Ocorrencia, prioridade_sugerida: bool) -> Self:
        """``prioridade_sugerida``: a prioridade veio da tabela de regras, não do agente."""
        return cls(
            ocorrencia_id=ocorrencia.id,
            status=ocorrencia.status.value,
            protocolo=ocorrencia.numero_protocolo,
            origem=ocorrencia.origem.value,
            prioridade=ocorrencia.prioridade.value,
            prioridade_sugerida=prioridade_sugerida,
            itens_apreendidos=len(ocorrencia.itens_apreendidos),
        )

    def dados_depois(self) -> dict[str, Any] | None:
        return {
            "status": self.status,
            "protocolo": self.protocolo,
            "origem": self.origem,
            "prioridade": self.prioridade,
            "prioridade_sugerida": self.prioridade_sugerida,
            "itens_apreendidos": self.itens_apreendidos,
        }


@dataclass(frozen=True, kw_only=True)
class OcorrenciaCorrigida(EventoOcorrencia):
    OPERACAO: ClassVar[str] = "ocorrencia.corrigir"

    versao_antes: int
    descricao_antes: str
    versao: int
    descricao: str

    @classmethod
    def de(cls, ocorrencia: Ocorrencia, versao_antes: int, descricao_antes: str) -> Self:
        return cls(
            ocorrencia_id=ocorrencia.id,
            versao_antes=versao_antes,
            descricao_antes=descricao_antes,
            versao=ocorrencia.versao,
            descricao=ocorrencia.descricao,
        )

    def dados_antes(self) -> dict[str, Any] | None:
        return {"versao": self.versao_antes, "descricao": self.descricao_antes}

    def dados_depois(self) -> dict[str, Any] | None:
        return {"versao": self.versao, "descricao": self.descricao}


@dataclass(frozen=True, kw_only=True)
class MudancaStatusOcorrencia(EventoOcorrencia):
    antes: SituacaoOcorrencia
    depois: SituacaoOcorrencia

    @classmethod
    def de(cls, ocorrencia: Ocorrencia, antes: SituacaoOcorrencia, **campos: Any) -> Self:
        return cls(ocorrencia_id=ocorrencia.id, antes=antes, depois=SituacaoOcorrencia.de(ocorrencia), **campos)

    def dados_antes(self) -> dict[str, Any] | None:
        return self.antes.como_dict()

    def dados_depois(self) -> dict[str, Any] | None:
        return self.depois.como_dict()


@dataclass(frozen=True, kw_only=True)
class OcorrenciaReenviada(MudancaStatusOcorrencia):
    OPERACAO: ClassVar[str] = "ocorrencia.reenviar"


@dataclass(frozen=True, kw_only=True)
class DecisaoSobreOcorrencia(MudancaStatusOcorrencia):
    # Nome do campo com o texto da decisão na trilha (o despacho, na validação).
    CAMPO_TEXTO: ClassVar[str] = "justificativa"

    texto: str | None

    @classmethod
    def de(cls, ocorrencia: Ocorrencia, antes: SituacaoOcorrencia, **campos: Any) -> Self:
        """O texto é o que a transição gravou no histórico de status."""
        texto = ocorrencia.historico_status[-1].justificativa
        return super().de(ocorrencia, antes, texto=texto, **campos)

    def dados_depois(self) -> dict[str, Any] | None:
        return {**self.depois.como_dict(), self.CAMPO_TEXTO: self.texto}


@dataclass(frozen=True, kw_only=True)
class OcorrenciaValidada(DecisaoSobreOcorrencia):
    OPERACAO: ClassVar[str] = "ocorrencia.validar"
    CAMPO_TEXTO: ClassVar[str] = "despacho"


@dataclass(frozen=True, kw_only=True)
class OcorrenciaDevolvidaParaCorrecao(DecisaoSobreOcorrencia):
    OPERACAO: ClassVar[str] = "ocorrencia.devolver_para_correcao"


@dataclass(frozen=True, kw_only=True)
class OcorrenciaRejeitada(DecisaoSobreOcorrencia):
    OPERACAO: ClassVar[str] = "ocorrencia.rejeitar"


@dataclass(frozen=True, kw_only=True)
class OcorrenciaArquivada(DecisaoSobreOcorrencia):
    OPERACAO: ClassVar[str] = "ocorrencia.arquivar"


@dataclass(frozen=True, kw_only=True)
class OcorrenciaExcluida(DecisaoSobreOcorrencia):
    OPERACAO: ClassVar[str] = "ocorrencia.excluir"


@dataclass(frozen=True, kw_only=True)
class OcorrenciaEncerrada(MudancaStatusOcorrencia):
    OPERACAO: ClassVar[str] = "ocorrencia.encerrar"

    desfecho: str | None
    viaturas_liberadas: tuple[str, ...]

    @classmethod
    def de(cls, ocorrencia: Ocorrencia, antes: SituacaoOcorrencia, viaturas_liberadas: Iterable[str] = ()) -> Self:
        return super().de(ocorrencia, antes, desfecho=ocorrencia.desfecho, viaturas_liberadas=tuple(viaturas_liberadas))

    def dados_depois(self) -> dict[str, Any] | None:
        return {"status": self.depois.status, "desfecho": self.desfecho, "viaturas_liberadas": list(self.viaturas_liberadas)}


@dataclass(frozen=True, kw_only=True)
class PrioridadeRedefinida(EventoOcorrencia):
    OPERACAO: ClassVar[str] = "ocorrencia.redefinir_prioridade"

    prioridade_antes: str
    versao_antes: int
    prioridade: str
    versao: int
    justificativa: str

    @classmethod
    def de(cls, ocorrencia: Ocorrencia, anterior: PrioridadeOcorrencia, versao_antes: int, justificativa: str) -> Self:
        return cls(
            ocorrencia_id=ocorrencia.id,
            prioridade_antes=anterior.value,
            versao_antes=versao_antes,
            prioridade=ocorrencia.prioridade.value,
            versao=ocorrencia.versao,
            justificativa=justificativa.strip(),
        )

    def dados_antes(self) -> dict[str, Any] | None:
        return {"prioridade": self.prioridade_antes, "versao": self.versao_antes}

    def dados_depois(self) -> dict[str, Any] | None:
        return {"prioridade": self.prioridade, "versao": self.versao, "justificativa": self.justificativa}


# --------------------------------------------- consulta pública ao documento (RF08)
TAMANHO_SUFIXO_AUDITADO = 4  # o código de verificação nunca é gravado por inteiro


@dataclass(frozen=True, kw_only=True)
class ConsultaDocumento(EventoAuditoria):
    """Consulta anônima ao documento oficial em ``/autenticar`` (UC08)."""

    ENTIDADE: ClassVar[str] = "DocumentoPolicial"

    ocorrencia_id: UUID | None
    tipo_codigo: str
    codigo_sufixo: str
    situacao: str | None

    @classmethod
    def de(cls, codigo: CodigoVerificacao, ocorrencia_id: UUID | None = None, situacao: SituacaoDocumento | None = None) -> Self:
        return cls(
            ocorrencia_id=ocorrencia_id,
            tipo_codigo=codigo.tipo.value,
            codigo_sufixo=codigo.valor[-TAMANHO_SUFIXO_AUDITADO:],
            situacao=situacao.value if situacao is not None else None,
        )

    def id_entidade(self) -> str | None:
        return str(self.ocorrencia_id) if self.ocorrencia_id else None

    def dados_depois(self) -> dict[str, Any] | None:
        dados: dict[str, Any] = {"tipo_codigo": self.tipo_codigo, "codigo_sufixo": self.codigo_sufixo}
        if self.situacao is not None:
            dados["situacao"] = self.situacao
        return dados


@dataclass(frozen=True, kw_only=True)
class DocumentoAutenticado(ConsultaDocumento):
    OPERACAO: ClassVar[str] = "documento.autenticar"


@dataclass(frozen=True, kw_only=True)
class SuspeitaDeFraudeDocumento(ConsultaDocumento):
    """O documento apresentado não confere com o hash emitido (ADULTERADO)."""

    OPERACAO: ClassVar[str] = "documento.suspeita_fraude"


@dataclass(frozen=True, kw_only=True)
class DocumentoNaoLocalizado(ConsultaDocumento):
    OPERACAO: ClassVar[str] = "documento.nao_localizado"
