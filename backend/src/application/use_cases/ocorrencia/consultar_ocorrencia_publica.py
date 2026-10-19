"""
Caso de uso: ConsultarOcorrenciaPublica (RF01 — acompanhamento do cidadão pelo protocolo).

Público por definição (sem ator). Só responde se o protocolo for de uma comunicação pública
e o código de acompanhamento conferir; qualquer falha devolve o mesmo "não encontrado", para
não servir de oráculo de enumeração. Ocorrência excluída logicamente é tratada como inexistente
(RNF03*: ela some das listagens) e a saída não carrega dados pessoais nem textos livres (LGPD).
"""
from application.ports.inbound.interface_consultar_ocorrencia_publica import (
    ConsultaPublicaOutput,
    InterfaceConsultarOcorrenciaPublica,
)
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from domain.ocorrencia.comunicacao_publica import codigo_acompanhamento_confere
from domain.ocorrencia.entity import Ocorrencia, OrigemOcorrencia
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import EntidadeNaoEncontradaError


class ConsultarOcorrenciaPublica(InterfaceConsultarOcorrenciaPublica):
    def __init__(self, repositorio: RepositorioOcorrencia) -> None:
        self._repositorio = repositorio

    async def executar(self, numero_protocolo: str, codigo_acompanhamento: str) -> ConsultaPublicaOutput:
        protocolo = (numero_protocolo or "").strip().upper()
        ocorrencia = await self._repositorio.buscar_por_protocolo(protocolo) if protocolo else None
        if ocorrencia is None or not _consultavel(ocorrencia, codigo_acompanhamento):
            raise EntidadeNaoEncontradaError(
                f"Protocolo {protocolo} não encontrado.", chave="ocorrencia.protocolo_nao_encontrado"
            )
        return ConsultaPublicaOutput(
            numero_protocolo=ocorrencia.numero_protocolo,
            status=ocorrencia.status.value,
            natureza=ocorrencia.natureza,
            localizacao=ocorrencia.localizacao,
            criada_em=ocorrencia.criada_em.isoformat(),
        )


def _consultavel(ocorrencia: Ocorrencia, codigo: str) -> bool:
    return (
        ocorrencia.origem == OrigemOcorrencia.PUBLICA
        and ocorrencia.status != StatusOcorrencia.EXCLUIDA
        and codigo_acompanhamento_confere(codigo, ocorrencia.codigo_acompanhamento_hash)
    )
