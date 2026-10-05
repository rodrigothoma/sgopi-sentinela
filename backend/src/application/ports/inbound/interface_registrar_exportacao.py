"""Porta de entrada: registro de exportação em massa (RNF03) — exportar dados é ato sensível e auditado."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from application.ports.inbound.ator import Ator


class RecursoExportavel(str, Enum):
    AUDITORIA = "auditoria"
    OCORRENCIAS = "ocorrencias"


@dataclass(frozen=True)
class RegistrarExportacaoInput:
    recurso: RecursoExportavel
    formato: str
    total_linhas: int
    filtros: dict[str, Any] = field(default_factory=dict)


class InterfaceRegistrarExportacao(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: RegistrarExportacaoInput) -> None:
        """Exige DELEGADO ou SUPERVISOR e grava quem exportou, o quê, com quais filtros e quantas linhas."""
        ...
