"""Porta de saída: GeradorNumeroSequencial (HEX-08) — numeração anual dos documentos oficiais.

Cada tipo de documento tem contador próprio por ano, que recomeça em 1 na virada do ano, e um
formato ``PREFIXO-AAAA-NNNNNN`` (protocolo SGOPI, inquérito IP, laudo LP, medida MP, ordem OD, ofício OFI).
"""
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import StrEnum


class TipoDocumentoSequencial(StrEnum):
    PROTOCOLO = "PROTOCOLO"
    INQUERITO = "INQUERITO"
    LAUDO = "LAUDO"
    MEDIDA_PROTETIVA = "MEDIDA_PROTETIVA"
    ORDEM_DESPACHO = "ORDEM_DESPACHO"
    OFICIO = "OFICIO"


def formatar_protocolo(ano: int, sequencial: int) -> str:
    return f"SGOPI-{ano:04d}-{sequencial:06d}"


def formatar_numero_inquerito(ano: int, sequencial: int) -> str:
    return f"IP-{ano:04d}-{sequencial:06d}"


def formatar_numero_laudo(ano: int, sequencial: int) -> str:
    return f"LP-{ano:04d}-{sequencial:06d}"


def formatar_numero_medida(ano: int, sequencial: int) -> str:
    return f"MP-{ano:04d}-{sequencial:06d}"


def formatar_numero_ordem(ano: int, sequencial: int) -> str:
    return f"OD-{ano:04d}-{sequencial:06d}"


def formatar_numero_oficio(ano: int, sequencial: int) -> str:
    return f"OFI-{ano:04d}-{sequencial:06d}"


Formatador = Callable[[int, int], str]

FORMATADORES: dict[TipoDocumentoSequencial, Formatador] = {
    TipoDocumentoSequencial.PROTOCOLO: formatar_protocolo,
    TipoDocumentoSequencial.INQUERITO: formatar_numero_inquerito,
    TipoDocumentoSequencial.LAUDO: formatar_numero_laudo,
    TipoDocumentoSequencial.MEDIDA_PROTETIVA: formatar_numero_medida,
    TipoDocumentoSequencial.ORDEM_DESPACHO: formatar_numero_ordem,
    TipoDocumentoSequencial.OFICIO: formatar_numero_oficio,
}


def formatar_numero_sequencial(tipo: TipoDocumentoSequencial, ano: int, sequencial: int) -> str:
    """Formato canônico do ``tipo``; compartilhado pelo adaptador SQL e pelas fakes de teste."""
    return FORMATADORES[tipo](ano, sequencial)


class GeradorNumeroSequencial(ABC):
    @abstractmethod
    async def proximo(self, tipo: TipoDocumentoSequencial, ano: int) -> str:
        """Devolve o próximo número formatado do ``tipo`` para o ``ano``.

        A contagem participa da transação corrente: dois chamadores concorrentes nunca recebem o
        mesmo número, e um rollback devolve o número ao contador.
        """
