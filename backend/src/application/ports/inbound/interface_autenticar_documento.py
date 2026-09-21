"""
Porta de entrada: autenticação pública de documento (RF08 / UC08).

Única porta do sistema sem ``Ator``: o consulente é anônimo (cidadão, advogado,
órgão externo — UC08 regra 1). Por isso a saída é um *espelho de conferência* —
nenhum dado pessoal dos envolvidos, nenhum endereço, nenhuma narrativa (RNF02, LGPD).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from application.ports.inbound.interface_consultar_ocorrencias import TipificacaoOutput


@dataclass(frozen=True)
class AutenticarDocumentoInput:
    """``codigo`` é a chave de 24 caracteres ou o hash SHA-256 impresso no documento."""

    codigo: str
    ip: str | None = None


@dataclass(frozen=True)
class DocumentoAutenticadoOutput:
    numero_protocolo: str
    situacao: str  # AUTENTICO | ADULTERADO | INDISPONIVEL
    chave_autenticidade: str
    emitido_em: str
    consultado_em: str
    natureza: str
    data_hora_fato: str
    status_ocorrencia: str
    hash_integridade: str
    tipificacoes: tuple[TipificacaoOutput, ...] = field(default_factory=tuple)
    envolvidos_por_tipo: dict[str, int] = field(default_factory=dict)
    quantidade_evidencias: int = 0


class InterfaceAutenticarDocumento(ABC):
    @abstractmethod
    async def executar(self, input_dto: AutenticarDocumentoInput) -> DocumentoAutenticadoOutput: ...
