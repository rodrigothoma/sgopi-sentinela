"""Eventos de auditoria da frota (RF02 · RNF03)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Self
from uuid import UUID

from domain.auditoria.evento import EventoAuditoria
from domain.viatura.entity import SituacaoViatura, Viatura


@dataclass(frozen=True, kw_only=True)
class EventoViatura(EventoAuditoria):
    ENTIDADE: ClassVar[str] = "Viatura"
    ENTIDADE_GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ("viaturas",)

    viatura_id: UUID

    def id_entidade(self) -> str | None:
        return str(self.viatura_id)


@dataclass(frozen=True, kw_only=True)
class ViaturaCadastrada(EventoViatura):
    OPERACAO: ClassVar[str] = "viatura.cadastrar"

    prefixo: str
    placa: str
    responsavel: str | None = None

    @classmethod
    def de(cls, viatura: Viatura) -> Self:
        return cls(viatura_id=viatura.id, prefixo=viatura.prefixo, placa=viatura.placa, responsavel=viatura.responsavel)

    def dados_depois(self) -> dict[str, Any] | None:
        return {"prefixo": self.prefixo, "placa": self.placa, "responsavel": self.responsavel}


@dataclass(frozen=True, kw_only=True)
class SituacaoViaturaAlterada(EventoViatura):
    """Alternância manual DISPONIVEL ⇄ INDISPONIVEL pelo Operador."""

    OPERACAO: ClassVar[str] = "viatura.alterar_situacao"

    situacao_antes: str
    situacao: str

    @classmethod
    def de(cls, viatura: Viatura, situacao_antes: SituacaoViatura) -> Self:
        return cls(viatura_id=viatura.id, situacao_antes=situacao_antes.value, situacao=viatura.situacao.value)

    def dados_antes(self) -> dict[str, Any] | None:
        return {"situacao": self.situacao_antes}

    def dados_depois(self) -> dict[str, Any] | None:
        return {"situacao": self.situacao}


@dataclass(frozen=True, kw_only=True)
class ViaturaChegouAoLocal(EventoViatura):
    """Chegada detectada pela telemetria: EM_DESLOCAMENTO → OPERANDO."""

    OPERACAO: ClassVar[str] = "viatura.chegada_ao_local"

    situacao: str
    ocorrencia_id: UUID
    numero_ordem: str
    distancia_metros: float
    origem: str

    @classmethod
    def de(cls, viatura: Viatura, ocorrencia_id: UUID, numero_ordem: str, distancia_metros: float, origem: str) -> Self:
        return cls(
            viatura_id=viatura.id,
            situacao=viatura.situacao.value,
            ocorrencia_id=ocorrencia_id,
            numero_ordem=numero_ordem,
            distancia_metros=round(distancia_metros, 1),
            origem=origem,
        )

    def dados_antes(self) -> dict[str, Any] | None:
        return {"situacao": SituacaoViatura.EM_DESLOCAMENTO.value}

    def dados_depois(self) -> dict[str, Any] | None:
        return {
            "situacao": self.situacao,
            "ocorrencia_id": str(self.ocorrencia_id),
            "numero_ordem": self.numero_ordem,
            "distancia_metros": self.distancia_metros,
            "origem": self.origem,
        }


@dataclass(frozen=True, kw_only=True)
class CredencialTelemetriaEmitida(EventoViatura):
    OPERACAO: ClassVar[str] = "viatura.emitir_credencial_telemetria"

    prefixo: str

    @classmethod
    def de(cls, viatura: Viatura) -> Self:
        return cls(viatura_id=viatura.id, prefixo=viatura.prefixo)

    def dados_depois(self) -> dict[str, Any] | None:
        return {"prefixo": self.prefixo}


@dataclass(frozen=True, kw_only=True)
class EventoCadastroViatura(EventoViatura):
    """Snapshots do cadastro preservados na trilha, inclusive após retirada da frota."""

    antes: dict[str, Any]
    depois: dict[str, Any]

    @classmethod
    def de(cls, viatura: Viatura, antes: dict[str, Any]) -> Self:
        """Captura identificação e exclusão sem depender da entidade mutável depois do ato."""
        return cls(viatura_id=viatura.id, antes=dict(antes), depois={
            "prefixo": viatura.prefixo, "placa": viatura.placa,
            "responsavel": viatura.responsavel, "ativo": viatura.ativo,
        })

    def dados_antes(self) -> dict[str, Any]:
        """Identificação vista pelo operador antes da alteração."""
        return dict(self.antes)

    def dados_depois(self) -> dict[str, Any]:
        """Cadastro resultante, sem expor referências mutáveis dos snapshots."""
        return dict(self.depois)


@dataclass(frozen=True, kw_only=True)
class CadastroViaturaEditado(EventoCadastroViatura):
    """Edição versionada de identificação e responsável."""

    OPERACAO: ClassVar[str] = "viatura.editar"


@dataclass(frozen=True, kw_only=True)
class CadastroViaturaExcluido(EventoCadastroViatura):
    """Exclusão lógica com preservação do cadastro na trilha."""

    OPERACAO: ClassVar[str] = "viatura.excluir"
