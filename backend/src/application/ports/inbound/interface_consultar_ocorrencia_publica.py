"""
Porta de entrada: InterfaceConsultarOcorrenciaPublica (RF01 — consulta do cidadão por protocolo).

Exige protocolo + código de acompanhamento (o protocolo é sequencial e adivinhável) e só
alcança comunicações de origem pública. Devolve somente dados não pessoais (RNF02 / LGPD):
nada de envolvidos, narrativa ou textos livres redigidos pelos policiais (justificativas, desfecho).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ConsultaPublicaOutput:
    numero_protocolo: str
    status: str
    natureza: str
    localizacao: str
    criada_em: str  # ISO 8601


class InterfaceConsultarOcorrenciaPublica(ABC):
    @abstractmethod
    async def executar(self, numero_protocolo: str, codigo_acompanhamento: str) -> ConsultaPublicaOutput: ...
